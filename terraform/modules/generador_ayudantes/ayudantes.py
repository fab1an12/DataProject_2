import os
import random
import json
import logging
import uuid
import time
from datetime import datetime
from google.cloud import pubsub_v1
from faker import Faker
from geopy.geocoders import Nominatim

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

PROJECT_ID = "edem24-25"#os.getenv("PROJECT_ID")
TOPIC_NAME = "prueba_help"#os.getenv("TOPIC_NAME")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

def generador_nombres():
    fake = Faker("es_ES")
    return fake.name()

def generador_telefonos():
    return f"6{random.randint(10000000, 99999999)}"

def generar_coordenadas_aleatorias():
    latitud = random.uniform(39.0, 40.1)
    longitud = random.uniform(-0.6, -0.15)
    return latitud, longitud

def identificar_pueblo(lat, lon):
    geolocator = Nominatim(user_agent="ayudante_geocoder")
    try:
        time.sleep(1)
        location = geolocator.reverse((lat, lon), language="es")
        if location and location.raw and "address" in location.raw:
            address = location.raw["address"]
            return address.get("city") or address.get("town") or address.get("village")
    except Exception as e:
        print("Error en reverse geocoding:", e)
    return "Valencia"

def generador_ayudantes():
    latitud, longitud = generar_coordenadas_aleatorias()
    pueblo = identificar_pueblo(latitud, longitud)
    recursos_ofrecidos = ["Refugio", "Suministros", "Atención médica", "Equipos de limpieza", "Rescate"]
    numero_min = 1
    numero_max = 10
    suministros = ["Agua", "Comida enlatada", "Mantas"]
    medico = ["Herida leve", "Fractura", "Deshidratación"]
    herramientas_limpieza = ["Pala", "Botas", "Cubo", "Mascarillas"]
    rescate = ["Rescate en edificio", "Rescate en vehículo", "Rescate en garaje"]
    
    datos = {
        "id": str(uuid.uuid4()),
        "Nombre": generador_nombres(),
        "Contacto": generador_telefonos(),
        "Tipo de necesidad": random.choice(recursos_ofrecidos),
        "Necesidad específica": random.choice(["Agua", "Comida enlatada", "Mantas", "Kit de higiene"]),
        "Nivel de urgencia": random.randint(1, 5),
        "Ubicación": {
            "pueblo": pueblo,
            "Latitud": latitud,
            "Longitud": longitud
        },
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    datos_json = json.dumps(datos, ensure_ascii=False)
    future = publisher.publish(topic_path, data=datos_json.encode("utf-8"))
    message_id = future.result()

    logging.info(f"Ayuda enviada a Pub/Sub con ID: {message_id}")
    logging.info(f"Datos enviados: {datos_json}")

if __name__ == "__main__":
    while True:
        generador_ayudantes()
