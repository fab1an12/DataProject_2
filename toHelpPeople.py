import os
import json
import random
import logging
from google.cloud import pubsub_v1
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROJECT_ID = "edem24-25"
PUBSUB_TOPIC = "prueba_help"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

TIPOS_NECESIDAD = ["Refugio", "Suministros", "Primeros auxilios", "Rescate"]
NUMERO_MIN = 1 
NUMERO_MAX = 10  

def obtener_ubicacion_aleatoria():
    geolocator = Nominatim(user_agent="ayudante_geocoder")
    lat = round(random.uniform(39.0, 39.75), 6)
    lon = round(random.uniform(-0.8, -0.2), 6)
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location:
            return {"latitud": lat, "longitud": lon}
    except GeocoderTimedOut:
        logging.warning("Timeout en geopy, usando coordenadas sin dirección.")
        return {"latitud": lat, "longitud": lon}

def generar_telefono():
    return f"6{random.randint(10000000, 99999999)}"

def generar_y_enviar_datos():
    datos = {
        "tipo_necesidad": random.choice(TIPOS_NECESIDAD),
        "ubicacion": obtener_ubicacion_aleatoria(),
        "numero_personas_afectadas": random.randint(NUMERO_MIN, NUMERO_MAX),
        "nivel_urgencia": random.randint(1, 5),
        "contacto": generar_telefono()
    }

    datos_json = json.dumps(datos)
    future = publisher.publish(topic_path, data=datos_json.encode("utf-8"))
    message_id = future.result()

    logging.info(f"Mensaje enviado a Pub/Sub con ID: {message_id}")
    logging.info(f"Datos enviados: {datos_json}")

if __name__ == "__main__":
    while True:
        generar_y_enviar_datos()