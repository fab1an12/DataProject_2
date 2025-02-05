import apache_beam as beam
import json
import logging
from apache_beam.options.pipeline_options import PipelineOptions

with open("config.json") as config_file:
    config = json.load(config_file)

project_id = config["project_id"]
subscription_name_solicitantes = config["subscription_name_solicitantes"]
subscription_name_ofertantes = config["subscription_name_ofertantes"]
bq_dataset = config["bq_dataset"]
bq_table = config["bq_table"]
bucket_name = config["bucket_name"]


table_reference = f"{project_id}:{bq_dataset}.{bq_table}"

def decode_message(msg):
    output = msg.decode('utf-8')
    return json.loads(output)

class AssignNumericKey(beam.DoFn):
    def process(self, element):
        yield (element['ubicacion'], element) 

def run():
    with beam.Pipeline(options=PipelineOptions(
        streaming=True,
        project=project_id,
        runner="DirectRunner",
        temp_location=f"gs://{bucket_name}/tmp",
        staging_location=f"gs://{bucket_name}/staging",
        region="europe-west6"
    )) as p:    
        solicitantes = (
            p
            | "ReadFromPubSub_Solicitantes" >> beam.io.ReadFromPubSub(subscription=f'projects/{project_id}/subscriptions/{subscription_name_solicitantes}')
            | "DecodeSolicitantes" >> beam.Map(decode_message)
            | "AssignKeySolicitantes"  >> beam.ParDo(AssignNumericKey())
        )
        ofertantes = (
            p
            | "ReadFromPubSub_Ofertantes" >> beam.io.ReadFromPubSub(subscription=f'projects/{project_id}/subscriptions/{subscription_name_ofertantes}')
            | "DecodeOfertantes" >> beam.Map(decode_message)
            | "AssignKeyOfertantes"  >> beam.ParDo(AssignNumericKey())
        )

        data = ((solicitantes, ofertantes) | beam.CoGroupByKey()
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                table=table_reference,
                schema="nombre:STRING, contacto:STRING, tipo_necesidad:STRING, ubicacion:STRING, numero_personas_afectadas:INTEGER, nivel_urgencia:INTEGER, match:STRING",
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
