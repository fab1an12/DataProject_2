import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
import logging
import json
import os
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)

def ParsePubSubMessages(message): 
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)
    logging.info(f"Mensaje parseado: {msg}")
    location = msg.get('Ubicación', {})
    normalized_msg = {
            'id': msg.get('id'),
            'name': msg.get('Nombre') or msg.get('name'),
            'contact': msg.get('Contacto') or msg.get('contact'),
            'necessity': msg.get('Tipo de ayuda') or msg.get('Tipo de necesidad') or msg.get('necessity'),
            'specific_need': msg.get('Ayuda específica') or msg.get('Necesidad específica') or msg.get('specific_need'),
            'urgency': int(msg.get('Nivel de urgencia',1)) or int(msg.get('urgency',1)),
            'city': location.get('Pueblo') or msg.get('city'),
            'location': {
                'latitude': float(location.get('Latitud',0)) or msg.get('latitude',0),
                'longitude': float(location.get('Longitud',0)) or msg.get('longitude',0)
            },
            'date': msg.get('Fecha') or msg.get('date'),
            'retry_count': int(msg.get('Nº_intentos', 0)) or int(msg.get('retry_count', 0)),
            'is_auto_generated': msg.get('Autogenerado', True) or msg.get('is_auto_generated', True)
        }
    logging.info(f"Mensaje normalizado: {normalized_msg}")
    return normalized_msg

def increment_processed(record):
    record['retry_count'] = record.get('retry_count', 0) + 1
    return record

def add_type(record, msg_type):
    record['type'] = msg_type
    return record

def key_by_match_fields(record):
    return ((record["necessity"], record["specific_need"], record["city"]), record)

class MatchedUnmatched(beam.DoFn):
    def process(self, element):
        key, grouped = element
        afectados = grouped['affected']
        voluntarios = grouped['volunteer']
        for afectado in afectados:
            found_any = False
            for voluntario in voluntarios:
                found_any = True
                yield beam.pvalue.TaggedOutput('matched', {'affected': afectado, 'volunteer': voluntario})
            if not found_any:
                yield beam.pvalue.TaggedOutput('non_matched_affected', afectado)
        if not afectados:
            for voluntario in voluntarios:
                yield beam.pvalue.TaggedOutput('non_matched_volunteer', voluntario)

def format_matched_for_pubsub(record):
    afectado = record.get("affected", {})
    voluntario = record.get("volunteer", {})
    formatted = {
        "match_id": afectado.get('id'),
        "affected_name": afectado.get("name", ""),
        "city": afectado.get("city", ""),
        "necessity": afectado.get("necessity", ""),
    }
    return json.dumps(formatted).encode("utf-8")

def format_unmatched_for_bq(record):
    current_time = datetime.now().isoformat()
    return {
        'id': record.get('id', 'UNKNOWN'),
        'necessity': record.get('necessity', 'UNKNOWN'),
        'specific_need': record.get('specific_need', 'UNKNOWN'),
        'city': record.get('city', 'UNKNOWN'),
        'last_attempt_date': current_time,
        'retry_count': record.get('retry_count',1),
        'urgency': record.get('urgency'),
        'latitude': record.get('location', {}).get('latitude'),
        'longitude': record.get('location', {}).get('longitude')
    }

def format_matched_for_bq(record):
    afectado = record['affected']
    voluntario = record['volunteer']
    current_time= datetime.now().isoformat()
    return {
        'match_id': f"{afectado.get('id', 'UNKNOWN')}-{voluntario.get('id', 'UNKNOWN')}",
        'affected_id': afectado.get('id', 'UNKNOWN'),
        'volunteer_id': voluntario.get('id', 'UNKNOWN'),
        'affected_necessity': afectado.get('necessity', 'UNKNOWN'),
        'affected_specific_need': afectado.get('specific_need', 'UNKNOWN'),
        'volunteer_necessity': voluntario.get('necessity', 'UNKNOWN'),
        'volunteer_specific_need': voluntario.get('specific_need', 'UNKNOWN'),
        'city': afectado.get('city', 'UNKNOWN'),
        'match_date': current_time,
        'status': 'MATCHED',
        'affected_urgency': afectado.get('urgency',0),
        'volunteer_urgency': voluntario.get('urgency',0),
        'affected_latitude': afectado.get('location', {}).get('latitude'),
        'affected_longitude': afectado.get('location', {}).get('longitude'),
        'volunteer_latitude': voluntario.get('location', {}).get('latitude'),
        'volunteer_longitude': voluntario.get('location', {}).get('longitude')
    }
    
def run():
    parser = argparse.ArgumentParser(description=('Input arguments for the Dataflow Streaming Pipeline.'))

    parser.add_argument(
                '--project_id',
                required=True,
                help='GCP cloud project name.')
    
    parser.add_argument(
                '--region',
                required=True,
                help='Region for the Dataflow job.')
    
    parser.add_argument(
                '--bq_dataset',
                required=True,
                help='PubSub Topic for sending push notifications.')
    
    parser.add_argument(
                '--bucket',
                required=True,
                help='Bucket for storing temporary files.')


    args = parser.parse_args()
       
    options = PipelineOptions(
        save_main_session=True,
        streaming=True,
        project=args.project_id,
        temp_location=f"gs://{args.bucket}/temp",
        staging_location=f"gs://{args.bucket}/stg",
        region=args.region,
        runner = "DataflowRunner",
        job_name = "cloudia"
    )
    matched_table_id   = f"{args.project_id}:{args.bq_dataset}.marched"
    unmatched_table_id = f"{args.project_id}:{args.bq_dataset}.unmatched"

    # Esquemas para BigQuery
    matched_schema = {
    'fields': [
        {'name': 'match_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'volunteer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_necessity', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'affected_specific_need', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'volunteer_necessity', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'volunteer_specific_need', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'city', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'match_date', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        {'name': 'status', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'affected_urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'volunteer_urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'affected_latitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'affected_longitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'volunteer_latitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'volunteer_longitude', 'type': 'FLOAT', 'mode': 'NULLABLE'}
    ]
    }
    
    unmatched_schema = {
    'fields': [
        {'name': 'id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'necessity', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'specific_need', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'city', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'last_attempt_date', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        {'name': 'retry_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'latitude', 'type': 'FLOAT', 'mode': 'NULLABLE'},
        {'name': 'longitude', 'type': 'FLOAT', 'mode': 'NULLABLE'}
    ]
    }

    with beam.Pipeline(options=options) as p:
        affected_data = (
            p
            | "ReadAffected" >> beam.io.ReadFromPubSub(subscription=f"projects/{args.project_id}/subscriptions/tohelp_subscription")
            | "ParseAffected" >> beam.Map(ParsePubSubMessages)
            | "MarkTypeAffected" >> beam.Map(add_type, "affected")
            | "IncrementProcessedAffected" >> beam.Map(increment_processed)
            | "WindowAffected" >> beam.WindowInto(window.FixedWindows(30))
            | "KeyAffected" >> beam.Map(key_by_match_fields)
        )
    
        # Lectura de mensajes de voluntarios
        volunteer_data = (
            p
            | "ReadVolunteers" >> beam.io.ReadFromPubSub(subscription=f"projects/{args.project_id}/subscriptions/helpers_subscription")
            | "ParseVolunteers" >> beam.Map(ParsePubSubMessages)
            | "MarkTypeVolunteer" >> beam.Map(add_type, "volunteer")
            | "IncrementProcessedVolunteer" >> beam.Map(increment_processed)
            | "WindowVolunteers" >> beam.WindowInto(window.FixedWindows(30))
            | "KeyVolunteers" >> beam.Map(key_by_match_fields)
        )
    
        # Agrupar por clave (ciudad, necesidad, disponibility)
        grouped = (
            {
                'affected': affected_data,
                'volunteer': volunteer_data
            }
            | "CoGroupByKey" >> beam.CoGroupByKey()
        )
    
        results = (
            grouped
            | "ProduceMatches" >> beam.ParDo(MatchedUnmatched())
              .with_outputs('matched', 'non_matched_affected', 'non_matched_volunteer')
        )
    
        matched_pcoll = results['matched']
        unmatched_affected_pcoll = results['non_matched_affected']
        unmatched_volunteer_pcoll = results['non_matched_volunteer']
    
        # Escribir coincidencias en BigQuery
        (
            matched_pcoll
            | "FormatMatchedForBQ" >> beam.Map(format_matched_for_bq)
            | "WriteMatchedToBQ" >> WriteToBigQuery(
                table=matched_table_id,
                schema=matched_schema,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_APPEND
            )
        )
    
        # Procesar no matcheados y re-publicar aquellos con processed < 7
        unmatched_affected_less_2 = unmatched_affected_pcoll | "FilterAff<2" >> beam.Filter(lambda x: x.get('processed', 0) < 2)
        unmatched_affected_ge_2   = unmatched_affected_pcoll | "FilterAff>=2" >> beam.Filter(lambda x: x.get('processed', 0) >= 2)
    
        unmatched_volunteer_less_2 = unmatched_volunteer_pcoll | "FilterVol<2" >> beam.Filter(lambda x: x.get('processed', 0) < 2)
        unmatched_volunteer_ge_2   = unmatched_volunteer_pcoll | "FilterVol>=2" >> beam.Filter(lambda x: x.get('processed', 0) >= 2)
    
        (
            unmatched_affected_less_2
            | "ReEncodeAff<2" >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | "RePublishAff<2" >> beam.io.WriteToPubSub(topic=f"projects/{args.project_id}/topics/tohelp_topic")
        )
        (
            unmatched_volunteer_less_2
            | "ReEncodeVol<2" >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | "RePublishVol<2" >> beam.io.WriteToPubSub(topic=f"projects/{args.project_id}/topics/helpers_topic")
        )
    
        unmatched_ge_2 = (
            (unmatched_affected_ge_2, unmatched_volunteer_ge_2)
            | "FlattenUnmatched>=2" >> beam.Flatten()
        )
    
        (
            unmatched_ge_2
            | "FormatUnmatchedForBQ" >> beam.Map(format_unmatched_for_bq)
            | "WriteUnmatchedToBQ" >> WriteToBigQuery(
                table=unmatched_table_id,
                schema=unmatched_schema,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=BigQueryDisposition.WRITE_APPEND
            )
        )
        
        matched_non_auto = (
            matched_pcoll
            | "FilterNonAuto" >> beam.Filter(lambda x: x.get("afectado", {}).get("is_auto_generated", True) is False)
        )

        (
            matched_non_auto
            | "FormatMatchForPubSub" >> beam.Map(format_matched_for_pubsub)
            | "WriteMatchNonAutoToPubSub" >> beam.io.WriteToPubSub(topic=f"projects/{args.project_id}/topics/return_topic")
        )

if __name__ == '__main__':
    logging.info("The process started")
    run()
    logging.info("Process finished")
