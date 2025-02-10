import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io.gcp.bigquery import BigQueryDisposition
from apache_beam.transforms.window import FixedWindows
from apache_beam.transforms.trigger import AfterProcessingTime, AccumulationMode
import json
import uuid
import logging
from datetime import datetime
from geopy.distance import geodesic

class ParsePubSubMessage(beam.DoFn):
    def process(self, message):
        record = json.loads(message.decode('utf-8'))
        clave = record.get("Tipo de ayuda")
        yield (clave, record)

class MatchOffersAndRequests(beam.DoFn):
    def process(self, element):
        tipo, (ofertas, demandas) = element
        resultados_match = []
        resultados_no_match = []

        for demanda in demandas:
            match_encontrado = False
            ubicacion_demanda = (demanda["Ubicación"]["Latitud"], demanda["Ubicación"]["Longitud"])

            for oferta in ofertas:
                ubicacion_oferta = (oferta["Ubicación"]["Latitud"], oferta["Ubicación"]["Longitud"])
                distancia = geodesic(ubicacion_demanda, ubicacion_oferta).kilometers

                if oferta["Tipo de necesidad"] == demanda["Tipo de ayuda"] and distancia <= 10:  # Máx. 10 km
                    match_id = str(uuid.uuid4())
                    match_data = {
                        "match_id": match_id,
                        "id_ofrece": oferta["id"],
                        "id_necesita": demanda["id"],
                        "nombre_ofrece": oferta["Nombre"],
                        "nombre_necesita": demanda["Nombre"],
                        "urgencia": demanda.get("Nivel de urgencia", 1),
                        "ubicacion_pueblo": demanda["Ubicación"]["pueblo"],
                        "distancia_km": distancia,
                        "fecha_match": datetime.utcnow().isoformat()
                    }
                    resultados_match.append(match_data)
                    match_encontrado = True
                    break  # Dejamos de buscar una vez encontrado un match

            if not match_encontrado:
                demanda["reintentos"] = demanda.get("reintentos", 0) + 1
                demanda["timestamp"] = datetime.utcnow().isoformat()
                resultados_no_match.append(demanda)

        yield beam.pvalue.TaggedOutput("matches", resultados_match)
        yield beam.pvalue.TaggedOutput("no_match", resultados_no_match)

def run(argv=None):
    # Definir las opciones del pipeline con el flag `allow_unsafe_triggers`
    pipeline_options = PipelineOptions()
    pipeline_options.view_as(StandardOptions).runner = 'DirectRunner'
    pipeline_options.view_as(StandardOptions).allow_unsafe_triggers = True  # Permitir triggers inseguros

    with beam.Pipeline(options=pipeline_options) as p:

        # Leer mensajes desde Pub/Sub
        p_ofrece = (
            p
            | "LeerOfrecePubSub" >> beam.io.ReadFromPubSub(topic='projects/alpine-alpha-447114-n9/topics/TOPIC_NAME_AYUDANTES')
            | "ParsearOfrece" >> beam.ParDo(ParsePubSubMessage())
            | "VentanaOfrece" >> beam.WindowInto(
                FixedWindows(60),  # Ventanas de 1 minuto
                trigger=AfterProcessingTime(10),  # Emisión después de 10 segundos
                accumulation_mode=AccumulationMode.DISCARDING  # No acumular datos previos
            )
        )

        p_necesita = (
            p
            | "LeerNecesitaPubSub" >> beam.io.ReadFromPubSub(topic='projects/alpine-alpha-447114-n9/topics/TOPIC_NAME_SOLICITANTES')
            | "ParsearNecesita" >> beam.ParDo(ParsePubSubMessage())
            | "VentanaNecesita" >> beam.WindowInto(
                FixedWindows(60),  # Ventanas de 1 minuto
                trigger=AfterProcessingTime(10),  # Emisión después de 10 segundos
                accumulation_mode=AccumulationMode.DISCARDING  # No acumular datos previos
            )
        )

        # Agrupar mensajes por clave y buscar matches
        resultados = (
            {"ofrece": p_ofrece, "necesita": p_necesita}
            | "CoGroupByKey" >> beam.CoGroupByKey()
            | "IntentarMatch" >> beam.ParDo(MatchOffersAndRequests()).with_outputs("matches", "no_match")
        )

        # Escribir matches a BigQuery
        resultados.matches | "EscribirMatches" >> beam.io.WriteToBigQuery(
            table="alpine-alpha-447114-n9:ayudas.matches",
            schema={
                "fields": [
                    {"name": "match_id", "type": "STRING", "mode": "REQUIRED"},
                    {"name": "id_ofrece", "type": "STRING", "mode": "REQUIRED"},
                    {"name": "id_necesita", "type": "STRING", "mode": "REQUIRED"},
                    {"name": "nombre_ofrece", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "nombre_necesita", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "urgencia", "type": "INTEGER", "mode": "NULLABLE"},
                    {"name": "ubicacion_pueblo", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "distancia_km", "type": "FLOAT", "mode": "NULLABLE"},
                    {"name": "fecha_match", "type": "TIMESTAMP", "mode": "REQUIRED"}
                ]
            },
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )

        # Escribir no matches a BigQuery
        resultados.no_match | "EscribirNoMatches" >> beam.io.WriteToBigQuery(
            table="alpine-alpha-447114-n9:ayudas.no_matches",
            schema={
                "fields": [
                    {"name": "id", "type": "STRING", "mode": "REQUIRED"},
                    {"name": "tipo", "type": "STRING", "mode": "REQUIRED"},
                    {"name": "reintentos", "type": "INTEGER", "mode": "REQUIRED"},
                    {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"}
                ]
            },
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
