import os
import json
import random
import logging
from google.cloud import pubsub_v1
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from faker import Faker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


with open('config.json', 'r') as f:
    config = json.load(f)

PROJECT_ID = config["PROJECT_ID"]
PUBSUB_TOPIC = config["PUBSUB_TOPIC_OFFER"]

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

TIPOS_AYUDA = ["Refugio", "Suministros", "Primeros auxilios", "Rescate"]
CAPACIDAD_MIN = 1 
CAPACIDAD_MAX = 10  

fake = Faker("es_ES")

def generador_nombres():
    return fake.name()

def obtener_ubicacion_aleatoria():
    geolocator = Nominatim(user_agent="geo_valencia")
    coordenadas = [
        (39.4699, -0.3763),
        (39.4828, -0.3945),
        (39.4370, -0.4650),
        (39.5950, -0.5319)
    ]
    lat, lon = random.choice(coordenadas)
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
        "nombre": generador_nombres(),
        "contacto": generar_telefono(),
        "tipo_ayuda": random.choice(TIPOS_AYUDA),
        "ubicacion": obtener_ubicacion_aleatoria(),
        "capacidad_asistencia": random.randint(CAPACIDAD_MIN, CAPACIDAD_MAX),
        "disponibilidad": random.choice(["Inmediata", "1-3 días", "Más de 3 días"]),
    }

    datos_json = json.dumps(datos, ensure_ascii=False)
    future = publisher.publish(topic_path, data=datos_json.encode("utf-8"))
    message_id = future.result()

    logging.info(f"Mensaje enviado a Pub/Sub con ID: {message_id}")
    logging.info(f"Datos enviados: {datos_json}")

if __name__ == "__main__":
    while True:
        generar_y_enviar_datos()
