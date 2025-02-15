import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.io.gcp.bigquery import WriteToBigQuery
import logging
import json
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

# BigQuery schemas
SUCCESSFUL_MATCHES_SCHEMA = {
    'fields': [
        {'name': 'match_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'volunteer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_necessity', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_specific_need', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'volunteer_necessity', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'volunteer_specific_need', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'city', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'match_date', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
        {'name': 'status', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'volunteer_urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'}
    ]
}

FAILED_MATCHES_SCHEMA = {
    'fields': [
        {'name': 'affected_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_necessity', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_specific_need', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'city', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'last_attempt_date', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
        {'name': 'retry_count', 'type': 'INTEGER', 'mode': 'REQUIRED'},
        {'name': 'final_status', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'details', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'affected_urgency', 'type': 'INTEGER', 'mode': 'NULLABLE'}
    ]
}

def safe_strip_upper(value):
    """Safely handles None values and applies strip and upper operations"""
    if value is None:
        return 'UNKNOWN'
    return str(value).strip().upper()

def ParsePubSubMessages(message):
    """
    Parses JSON messages from Pub/Sub with improved error handling
    and None value management
    """
    try:
        pubsub_message = message.decode('utf-8')
        logging.info(f"Mensaje recibido: {pubsub_message}")
       
        msg = json.loads(pubsub_message)
        logging.info(f"Mensaje parseado: {msg}")

        # Extract location data safely
        location = msg.get('Ubicación', {})
        if not isinstance(location, dict):
            location = {}

        # Detect if message is auto-generated
        is_auto_generated = (
            msg.get('Autogenerado', False) == True or
            str(msg.get('id', '')).startswith('V-') or
            str(msg.get('id', '')).startswith('AUTO_')
        )

        # Normalized message with safe value handling
        normalized_msg = {
            'id': msg.get('id', f"AUTO_{datetime.utcnow().isoformat()}"),
            'name': msg.get('Nombre'),
            'contact': msg.get('Contacto'),
            'necessity': safe_strip_upper(msg.get('Tipo de ayuda') or msg.get('Tipo de necesidad')),
            'specific_need': safe_strip_upper(msg.get('Ayuda específica') or msg.get('Necesidad específica')),
            'urgency': int(msg.get('Nivel de urgencia', 0)),
            'city': safe_strip_upper(location.get('pueblo')),
            'location': {
                'latitude': float(location.get('Latitud', 0.0)),
                'longitude': float(location.get('Longitud', 0.0))
            },
            'date': msg.get('Fecha', datetime.utcnow().isoformat()),
            'retry_count': int(msg.get('retry_count', 0)),
            # Añadimos un campo para rastrear si es auto-generado
            'is_auto_generated': is_auto_generated
        }
       
        logging.info(f"Mensaje normalizado: {normalized_msg}")
        return normalized_msg
    except Exception as e:
        logging.error(f"Error procesando mensaje: {e}")
        logging.error(f"Mensaje que causó el error: {message}")
        raise

class ProduceMatchesWithRetry(beam.DoFn):
    """Matches affected people with volunteers and handles retries"""
    def process(self, element):
        try:
            key, grouped = element
            affected = list(grouped.get('affected', []))
            volunteers = list(grouped.get('volunteer', []))

            logging.info(f"🔍 Intentando emparejar clave {key} con {len(affected)} afectados y {len(volunteers)} voluntarios.")
           
            current_time = datetime.utcnow().isoformat()

            for afectado in affected:
                if not isinstance(afectado, dict):
                    logging.error(f"Afectado inválido: {afectado}")
                    continue

                matched = False
                # Obtén el retry_count existente o inicializa en 0
                retry_count = int(afectado.get('retry_count', 0))
                is_auto_generated = afectado.get('is_auto_generated', False)

                for voluntario in volunteers:
                    if not isinstance(voluntario, dict):
                        logging.error(f"Voluntario inválido: {voluntario}")
                        continue

                    logging.info(f"🔎 Comparando: Afectado {afectado.get('necessity')} - {afectado.get('specific_need')} "
                                f"con Voluntario {voluntario.get('necessity')} - {voluntario.get('specific_need')}")

                    if (afectado.get('necessity') == voluntario.get('necessity') and
                        afectado.get('specific_need') == voluntario.get('specific_need')):
                       
                        matched = True
                        successful_match = {
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
                            'affected_urgency': afectado.get('urgency'),
                            'volunteer_urgency': voluntario.get('urgency')
                        }
                        logging.info(f"✅ Match encontrado: {successful_match}")
                       
                        # Write to BigQuery
                        yield beam.pvalue.TaggedOutput('successful_matches', successful_match)
                       
                        # Only send AUTO-GENERATED matches to PubSub
                        if is_auto_generated:
                            pubsub_message = {
                                **successful_match,
                                'affected_data': afectado,
                                'volunteer_data': voluntario
                            }
                            yield beam.pvalue.TaggedOutput('pubsub_matches', pubsub_message)
                       
                        volunteers.remove(voluntario)
                        break

                if not matched:
                    # Incrementa el retry_count
                    retry_count += 1
                   
                    failed_match = {
                        'affected_id': afectado.get('id', 'UNKNOWN'),
                        'affected_necessity': afectado.get('necessity', 'UNKNOWN'),
                        'affected_specific_need': afectado.get('specific_need', 'UNKNOWN'),
                        'city': afectado.get('city', 'UNKNOWN'),
                        'last_attempt_date': current_time,
                        'retry_count': 3 if retry_count >= 3 else retry_count,  # Siempre 3 si supera 3 intentos
                        'final_status': 'PENDING_RETRY' if retry_count < 3 else 'FAILED_AFTER_RETRIES',
                        'details': f"No se encontró voluntario después de {retry_count} intentos",
                        'affected_urgency': afectado.get('urgency')
                    }
                    logging.info(f"❌ No-match registrado: {failed_match}")
                    yield beam.pvalue.TaggedOutput('failed_matches', failed_match)
        except Exception as e:
            logging.error(f"Error en ProduceMatchesWithRetry: {e}")
            raise

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

    try:
        with beam.Pipeline(options=options) as p:
            window_size = 90

            # Read and process affected people data
            affected_data = (
                p
                | "Read affected" >> beam.io.ReadFromPubSub(subscription=args.affected_sub)
                | "Parse affected" >> beam.Map(ParsePubSubMessages)
                | "Window affected" >> beam.WindowInto(window.FixedWindows(window_size))
                | "Key affected" >> beam.Map(lambda x: (
                    (x['necessity'], x['specific_need'], x['city']), x))
            )

            # Read and process volunteer data
            volunteer_data = (
                p
                | "Read volunteer" >> beam.io.ReadFromPubSub(subscription=args.volunteer_sub)
                | "Parse volunteer" >> beam.Map(ParsePubSubMessages)
                | "Window volunteer" >> beam.WindowInto(window.FixedWindows(window_size))
                | "Key volunteer" >> beam.Map(lambda x: (
                    (x['necessity'], x['specific_need'], x['city']), x))
            )

            # Perform matching
            results = (
                {'affected': affected_data, 'volunteer': volunteer_data}
                | "CoGroupByKey" >> beam.CoGroupByKey()
                | "Match" >> beam.ParDo(ProduceMatchesWithRetry())
                    .with_outputs('pubsub_matches', 'successful_matches', 'failed_matches')
            )

            # Write successful matches to BigQuery
            (results.successful_matches | "Write Successful Matches" >> WriteToBigQuery(
                f"{args.project_id}:{args.bigquery_dataset}.successful_matches",
                schema=SUCCESSFUL_MATCHES_SCHEMA,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            ))

            # Write failed matches to BigQuery
            (results.failed_matches | "Write Failed Matches" >> WriteToBigQuery(
                f"{args.project_id}:{args.bigquery_dataset}.failed_matches",
                schema=FAILED_MATCHES_SCHEMA,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            ))

            # Write AUTO-GENERATED matches to PubSub
            (results.pubsub_matches
             | "Convert to JSON" >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
             | "Write to PubSub" >> beam.io.WriteToPubSub(topic=args.output_topic_matched))

    except Exception as e:
        logging.error(f"Error en el pipeline principal: {e}")
        raise

if __name__ == '__main__':
    logging.info("🚀 Iniciando pipeline...")
    run()
