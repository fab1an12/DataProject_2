import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
import logging
import json
import argparse

# Configurar logging
logging.basicConfig(level=logging.INFO)

def ParsePubSubMessages(message): 
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)

    logging.info(f"Mensaje recibido de Pub/Sub: {msg}")

    return msg

def key_by_match_fields(record):
    """
    Returns a tuple: (
        (city, necessity, disponibility),
        record
    )
    Maneja casos donde faltan claves en el mensaje.
    """
    city = record.get("city", "UNKNOWN")  # Si no tiene "city", usa "UNKNOWN"
    necessity = record.get("necessity", "UNKNOWN")
    disponibility = record.get("disponibility", "UNKNOWN")

    key = (city, necessity, disponibility)
    logging.info(f"Generando clave: {key} para el record: {record}")

    return key, record

def produce_matches(element):
    """
    Recibe algo como:
        element = ( key, { 'affected': [...], 'volunteer': [...] } )
    y produce:
        - Todos los pares (afectado, voluntario) emparejados
        - Todos los afectados sin voluntarios
        - Todos los voluntarios sin afectados
    """
    key, grouped = element
    afectados = grouped.get('affected', [])
    voluntarios = grouped.get('volunteer', [])

    logging.info(f"Procesando clave {key} con {len(afectados)} afectados y {len(voluntarios)} voluntarios.")

    for afectado in afectados:
        found_any = False
        for voluntario in voluntarios:
            found_any = True
            yield beam.pvalue.TaggedOutput(
                'matched',
                {'afectado': afectado, 'voluntario': voluntario}
            )
        if not found_any:
            yield beam.pvalue.TaggedOutput('non_matched_affected', afectado)

    if not afectados:
        for voluntario in voluntarios:
            yield beam.pvalue.TaggedOutput('non_matched_volunteer', voluntario)

def run():
    logging.info("Iniciando el pipeline de Dataflow...")

    parser = argparse.ArgumentParser(description='Input arguments for the Dataflow Streaming Pipeline.')
    
    parser.add_argument('--project_id', required=True, help='GCP cloud project name')
    parser.add_argument('--affected_sub', required=True, help='PubSub subscription for affected')
    parser.add_argument('--volunteer_sub', required=True, help='PubSub subscription for volunteers')
    parser.add_argument('--output_topic_non_matched', required=True, help='Output Pub/Sub topic for non-matched')
    parser.add_argument('--output_topic_matched', required=True, help='Output Pub/Sub topic for matched')
    parser.add_argument('--runner', default='DirectRunner', help='Runner for execution')
    parser.add_argument('--region', default='europe-west1', help='GCP region')
    parser.add_argument('--temp_location', required=True, help='GCS temp location')
    parser.add_argument('--staging_location', required=True, help='GCS staging location')

    args, pipeline_opts = parser.parse_known_args()

    logging.info(f"Proyecto: {args.project_id}")
    logging.info(f"Affected Subscription: {args.affected_sub}")
    logging.info(f"Volunteer Subscription: {args.volunteer_sub}")
    logging.info(f"Output Topic (non-matched): {args.output_topic_non_matched}")
    logging.info(f"Output Topic (matched): {args.output_topic_matched}")
    logging.info(f"Runner: {args.runner}")
    logging.info(f"Región: {args.region}")

    options = PipelineOptions(
        pipeline_opts,
        save_main_session=True,
        runner="DataflowRunner",  # Corrección: usar string
        streaming=True,
        project=args.project_id,
        region=args.region,
        temp_location=args.temp_location,
        staging_location=args.staging_location,
        experiments=["use_runner_v2"]  # Mejora para compatibilidad
    )

    with beam.Pipeline(options=options) as p:
        logging.info("Creando el pipeline...")

        affected_data = (
            p
            | "Read affected data from Pub/Sub" >> beam.io.ReadFromPubSub(subscription=args.affected_sub)
            | "Parse Affected" >> beam.Map(ParsePubSubMessages)
            | "Window Affected" >> beam.WindowInto(beam.window.FixedWindows(90))
            | "Key Affected" >> beam.Map(key_by_match_fields)
        )

        volunteer_data = (
            p
            | "Read volunteer data from Pub/Sub" >> beam.io.ReadFromPubSub(subscription=args.volunteer_sub)
            | "Parse Volunteer" >> beam.Map(ParsePubSubMessages)
            | "Window Volunteer" >> beam.WindowInto(beam.window.FixedWindows(90))
            | "Key Volunteer" >> beam.Map(key_by_match_fields)
        )

        logging.info("Unificando datos de afectados y voluntarios...")

        grouped = (
            {'affected': affected_data, 'volunteer': volunteer_data}
            | "CoGroupByKey" >> beam.CoGroupByKey()
        )

        results = (
            grouped
            | "Match DoFn" >> beam.ParDo(produce_matches)
              .with_outputs('matched', 'non_matched_affected', 'non_matched_volunteer')
        )

        matched_pcoll = results['matched']
        unmatched_affected_pcoll = results['non_matched_affected']
        unmatched_volunteer_pcoll = results['non_matched_volunteer']

        logging.info("Escribiendo los datos procesados en Pub/Sub...")

        (matched_pcoll
         | 'Convert matched to JSON' >> beam.Map(lambda x: json.dumps(x).encode("utf-8"))
         | 'Write matched data' >> beam.io.WriteToPubSub(topic=args.output_topic_matched)
        )

        (unmatched_affected_pcoll
         | 'Convert non-matched affected to JSON' >> beam.Map(lambda x: json.dumps(x).encode("utf-8"))
         | 'Write non-matched affected'>> beam.io.WriteToPubSub(topic=args.output_topic_non_matched)
        )

        (unmatched_volunteer_pcoll
         | 'Convert non-matched volunteers to JSON' >> beam.Map(lambda x: json.dumps(x).encode("utf-8"))
         | 'Write non-matched volunteers'>> beam.io.WriteToPubSub(topic=args.output_topic_non_matched)
        )

        logging.info("Pipeline finalizado exitosamente.")

if __name__ == '__main__':
    logging.info("Ejecutando el script...")
    run()



'''(.venv) raulalgora@MacBook-Pro-de-Raul-2 dataflow % python3 dataflow.py \
    --project_id alpine-alpha-447114-n9 \
    --affected_sub projects/alpine-alpha-447114-n9/subscriptions/affected-sub \
    --volunteer_sub projects/alpine-alpha-447114-n9/subscriptions/volunteer-sub \
    --output_topic_non_matched projects/alpine-alpha-447114-n9/topics/no-matched \
    --output_topic_matched projects/alpine-alpha-447114-n9/topics/matched \
    --runner DataflowRunner \
    --region europe-west1 \
    --zone europe-west1-b \
    --temp_location gs://dataflow_raulalgora_west1/tmp \
    --staging_location gs://dataflow_raulalgora_west1/stg \
    --service_account_email xxx-compute@developer.gserviceaccount.com
'''