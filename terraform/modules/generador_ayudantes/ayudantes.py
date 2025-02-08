import os
import random
import json
import logging
import uuid
from datetime import datetime
from google.cloud import pubsub_v1
from faker import Faker
from shapely.geometry import Point, shape
from pyproj import Transformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

with open('config.json', 'r') as f:
    config = json.load(f)

project_id = config["project_id"]
topic_name = config["topic_name"]

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

# Nombres
fake = Faker("es_ES")
def generador_nombres():
    return fake.name()

# Contactos
def generador_telefonos():
    return f"6{random.randint(10000000, 99999999)}"

# Recursos
recursos_ofrecidos = ["Refugio", "Suministros", "Atención médica", "Equipos de limpieza", "Asistencia psicológica"]
suministros = ["Agua", "Comida enlatada", "Mantas", "Kit de higiene"]
atencion_medica= ["Herida leve", "Fractura", "Deshidratación"]
herramientas_limpieza = ["Pala", "Botas", "Cubo", "Mascarillas", "Manguera", "Escoba industrial"]
especialistas_psicologicos = ["Psicólogo", "Voluntario capacitado", "Trabajador social"]

# Ubicación
with open('zonas_valencia.geojson', 'r', encoding='utf-8') as f:
    datos_zonas = json.load(f)

zonas = {}
for municipio in datos_zonas["features"]:
    nombre = municipio["properties"]["NOMBRE"]
    poligono = shape(municipio["geometry"])
    zonas[nombre] = poligono

transformer = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)

def generar_coordenadas_aleatorias():
    latitud = random.uniform(39.0, 40.1)
    longitud = random.uniform(-0.6, -0.15)
    return latitud, longitud

def identificar_pueblo(lat, lon):
    lon_25830, lat_25830 = transformer.transform(lon, lat)

    punto = Point(lon_25830, lat_25830)
    for pueblo, poligono in zonas.items():
        if poligono.contains(punto):
            return pueblo
    return "Pueblo desconocido"

# Datos ayudantes
def generador_ayudantes():
    latitud, longitud = generar_coordenadas_aleatorias()
    pueblo = identificar_pueblo(latitud, longitud)

    datos = {
        "id": str(uuid.uuid4()),
        "Nombre": generador_nombres(),
        "Contacto": generador_telefonos(),
        "Tipo de necesidad": random.choice(recursos_ofrecidos),
        "Nivel de urgencia": random.randint(1, 5),
        "Ubicación": {
            "pueblo": pueblo,
            "Latitud": latitud,
            "Longitud": longitud
        },
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if recursos_ofrecidos == "Refugio":
        datos["Capacidad de personas"] = random.randint(1, 5)

    elif recursos_ofrecidos == "Suministros":
        datos["Duración del suministro (días)"] = random.randint(1, 7)
        datos["Tipo de suministro"] = random.choice(suministros)

    elif recursos_ofrecidos == "Atención médica":
        datos["Especialización médica"] = random.choice(atencion_medica)

    elif recursos_ofrecidos == "Equipos de limpieza":
        datos["Herramientas disponibles"] = random.choice(herramientas_limpieza)

    elif recursos_ofrecidos == "Asistencia psicológica":
        datos["Especialista disponible"] = random.choice(especialistas_psicologicos)


    datos_json = json.dumps(datos, ensure_ascii=False)
    future = publisher.publish(topic_path, data=datos_json.encode("utf-8"))
    message_id = future.result()

    logging.info(f"Ayuda enviada a Pub/Sub con ID: {message_id}")
    logging.info(f"Datos enviados: {datos_json}")

if __name__ == "__main__":
    while True:
        generador_ayudantes()
