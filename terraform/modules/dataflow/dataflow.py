import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.io.gcp.bigquery import WriteToBigQuery
import logging
import json
import argparse
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Esquema de BigQuery
SUCCESSFUL_MATCHES_SCHEMA = """
    match_id:STRING, 
    affected_id:STRING, 
    volunteer_id:STRING, 
    necessity:STRING, 
    specific_need:STRING, 
    city:STRING, 
    match_date:TIMESTAMP, 
    status:STRING
"""

FAILED_MATCHES_SCHEMA = """
    affected_id:STRING, 
    necessity:STRING, 
    specific_need:STRING, 
    city:STRING, 
    last_attempt_date:TIMESTAMP, 
    retry_count:INTEGER, 
    final_status:STRING, 
    details:STRING
"""

def ParsePubSubMessages(message): 
    """Parses JSON messages from Pub/Sub"""
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)

    # ✅ Normalización de los datos para evitar errores de comparación
    normalized_msg = {
        'id': msg.get('id'),
        'name': msg.get('Nombre'),
        'contact': msg.get('Contacto'),
        'necessity': msg.get('Tipo de ayuda', msg.get('Tipo de necesidad', 'UNKNOWN')).strip().upper(),
        'specific_need': msg.get('Ayuda específica', msg.get('Necesidad específica', 'UNKNOWN')).strip().upper(),
        'urgency': msg.get('Nivel de urgencia', 0),
        'city': msg.get('Ubicación', {}).get('pueblo', 'UNKNOWN').strip().upper(),
        'location': {
            'latitude': msg.get('Ubicación', {}).get('Latitud', 0.0),
            'longitude': msg.get('Ubicación', {}).get('Longitud', 0.0)
        },
        'date': msg.get('Fecha', datetime.utcnow().isoformat()),  
        'retry_count': msg.get('retry_count', 0)
    }
    
    logging.info(f"Mensaje normalizado: {normalized_msg}")
    return normalized_msg

class ProduceMatchesWithRetry(beam.DoFn):
    """Matches affected people with volunteers and handles retries"""
    def process(self, element):
        key, grouped = element
        affected = list(grouped.get('affected', []))
        volunteers = list(grouped.get('volunteer', []))

        logging.info(f"🔍 Intentando emparejar clave {key} con {len(affected)} afectados y {len(volunteers)} voluntarios.")
        
        current_time = datetime.utcnow().isoformat()  

        for afectado in affected:
            matched = False
            retry_count = afectado.get('retry_count', 0)

            for voluntario in volunteers:
                logging.info(f"🔎 Comparando: Afectado {afectado['necessity']} - {afectado['specific_need']} "
                             f"con Voluntario {voluntario['necessity']} - {voluntario['specific_need']}")

                if (afectado['necessity'] == voluntario['necessity'] and 
                    afectado['specific_need'] == voluntario['specific_need']):
                    
                    matched = True
                    successful_match = {
                        'match_id': f"{afectado['id']}-{voluntario['id']}",
                        'affected_id': afectado['id'],
                        'volunteer_id': voluntario['id'],
                        'necessity': afectado['necessity'],
                        'specific_need': afectado['specific_need'],
                        'city': afectado['city'],
                        'match_date': current_time,
                        'status': 'MATCHED'
                    }
                    logging.info(f"✅ Match encontrado: {successful_match}")
                    yield beam.pvalue.TaggedOutput('successful_matches', successful_match)
                    yield beam.pvalue.TaggedOutput('matched', successful_match)
                    volunteers.remove(voluntario)
                    break  

            if not matched:
                retry_count += 1
                afectado['retry_count'] = retry_count
                
                failed_match = {
                    'affected_id': afectado['id'],
                    'necessity': afectado['necessity'],
                    'specific_need': afectado['specific_need'],
                    'city': afectado['city'],
                    'last_attempt_date': current_time,
                    'retry_count': retry_count,
                    'final_status': 'PENDING_RETRY' if retry_count < 3 else 'FAILED_AFTER_RETRIES',
                    'details': f"No se encontró voluntario después de {retry_count} intentos"
                }
                logging.info(f"❌ No-match registrado: {failed_match}")
                yield beam.pvalue.TaggedOutput('failed_matches', failed_match)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id', required=True)
    parser.add_argument('--affected_sub', required=True)
    parser.add_argument('--volunteer_sub', required=True)
    parser.add_argument('--output_topic_matched', required=True)
    parser.add_argument('--bigquery_dataset', required=True)
    parser.add_argument('--temp_location', required=True)
    parser.add_argument('--staging_location', required=True)

    args, pipeline_opts = parser.parse_known_args()

    options = PipelineOptions(
        pipeline_opts,
        save_main_session=True,
        streaming=True,
        project=args.project_id,
        temp_location=args.temp_location,
        staging_location=args.staging_location
    )

    with beam.Pipeline(options=options) as p:
        window_size = 90

        affected_data = (
            p
            | "Read affected" >> beam.io.ReadFromPubSub(subscription=args.affected_sub)
            | "Parse affected" >> beam.Map(ParsePubSubMessages)
            | "Window affected" >> beam.WindowInto(window.FixedWindows(window_size))  
            | "Key affected" >> beam.Map(lambda x: (
                (x['necessity'], x['specific_need'], x['city']), x))
        )

        volunteer_data = (
            p
            | "Read volunteer" >> beam.io.ReadFromPubSub(subscription=args.volunteer_sub)
            | "Parse volunteer" >> beam.Map(ParsePubSubMessages)
            | "Window volunteer" >> beam.WindowInto(window.FixedWindows(window_size))  
            | "Key volunteer" >> beam.Map(lambda x: (
                (x['necessity'], x['specific_need'], x['city']), x))
        )

        results = (
            {'affected': affected_data, 'volunteer': volunteer_data}
            | "CoGroupByKey" >> beam.CoGroupByKey()
            | "Match" >> beam.ParDo(ProduceMatchesWithRetry())
                .with_outputs('matched', 'successful_matches', 'failed_matches')
        )

        (results.successful_matches | "Write Successful Matches" >> WriteToBigQuery(
            f"{args.project_id}:{args.bigquery_dataset}.successful_matches",
            schema=SUCCESSFUL_MATCHES_SCHEMA,
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_APPEND"
        ))

        (results.failed_matches | "Write Failed Matches" >> WriteToBigQuery(
            f"{args.project_id}:{args.bigquery_dataset}.failed_matches",
            schema=FAILED_MATCHES_SCHEMA,
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_APPEND"
        ))

if __name__ == '__main__':
    logging.info("🚀 Iniciando pipeline...")
    run()



'''(.venv) raulalgora@MacBook-Pro-de-Raul-2 dataflow % python3 dataflow.py \
    --project_id xxxx \
    --affected_sub projects/alpine-alpha-447114-n9/subscriptions/affected-sub \
    --volunteer_sub projects/alpine-alpha-447114-n9/subscriptions/volunteer-sub \
    --output_topic_matched projects/alpine-alpha-447114-n9/topics/matched \
    --runner DataflowRunner \
    --region europe-west1 \
    --worker_zone europe-west1-b \
    --temp_location gs://dataflow_raulalgora_west1/tmp \
    --staging_location gs://dataflow_raulalgora_west1/stg \
    --service_account_email xxxxx@developer.gserviceaccount.com \
    --bigquery_dataset dataflow

HOLI

''' 