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

PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("TOPIC_NAME_AYUDANTES")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

def generador_nombres():
    fake = Faker("es_ES")
    return fake.name()

def generador_telefonos():
    return f"6{random.randint(10000000, 99999999)}"

def generar_coordenadas_aleatorias():
    latitud = random.uniform(39.38, 39.46)
    longitud = random.uniform(-0.45, -0.34)
    return latitud, longitud

def identificar_pueblo(lat, lon):
    pueblos = {
        'Paiporta': ((39.40, 39.42), (-0.40, -0.38)),
        'Picanya': ((39.41, 39.43), (-0.42, -0.40)),
        'Benetússer': ((39.39, 39.41), (-0.38, -0.36)),
        'Aldaia': ((39.43, 39.45), (-0.45, -0.43)),
        'Torrent': ((39.42, 39.44), (-0.43, -0.41)),
        'Quart de Poblet': ((39.44, 39.46), (-0.41, -0.39)),
        'Mislata': ((39.38, 39.40), (-0.36, -0.34)),
        'Xirivella': ((39.41, 39.43), (-0.38, -0.36))
    }
    
    for pueblo, ((lat_min, lat_max), (lon_min, lon_max)) in pueblos.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return pueblo
    
    return "Valencia"

def generador_ayudantes():
    latitud, longitud = generar_coordenadas_aleatorias()
    pueblo = identificar_pueblo(latitud, longitud)
    recursos_ofrecidos = {
        "Agua": {
            "items": ["Botella de agua", "Garrafa 20 litros", "Bidón 5 litros"],
            "peso": 50
        },
        "Alimentos": {
            "items": ["Comida enlatada", "Alimentos no perecederos", "Comida preparada"],
            "peso": 30
        },
        "Medicamentos": {
            "items": ["Analgésicos", "Antibióticos", "Medicamentos para la gripe"],
            "peso": 15
        },
        "Otros": {
            "items": ["Ropa", "Linternas", "Pilas", "Herramientas"],
            "peso": 5
        }
    }
    tipos = list(recursos_ofrecidos.keys())
    pesos = [recursos_ofrecidos[tipo]["peso"] for tipo in tipos]
    tipo_necesidad = random.choices(tipos, weights=pesos, k=1)[0]
    necesidad_especifica = random.choice(recursos_ofrecidos[tipo_necesidad]["items"])
    datos = {
        "id": "V-" + str(uuid.uuid4()),
        "Nombre": generador_nombres(),
        "Contacto": generador_telefonos(),
        "Tipo de necesidad": tipo_necesidad,
        "Necesidad específica": necesidad_especifica,
        "Nivel de urgencia": random.randint(1, 5),
        "Ubicación": {
            "Pueblo": pueblo,
            "Latitud": latitud,
            "Longitud": longitud
        },
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Autogenerado": True,
        "Nº_intentos": 0
    }

    datos_json = json.dumps(datos, ensure_ascii=False)
    future = publisher.publish(topic_path, data=datos_json.encode("utf-8"))
    message_id = future.result()

    logging.info(f"Ayuda enviada a Pub/Sub con ID: {message_id}")
    logging.info(f"Datos enviados: {datos_json}")
    time.sleep(2)

if __name__ == "__main__":
    while True:
        generador_ayudantes()
