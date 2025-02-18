import json
from datetime import datetime
from geopy.geocoders import Nominatim
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from google.cloud import pubsub_v1

class PubSubPayload(BaseModel):
    nombre: str = Field(..., description="Name of the person in need of help")
    tipo_necesidad: str = Field(..., description="Type of help needed: Agua, Alimentos, Medicamentos, u Otros.")
    necesidad_especifica: str = Field(..., description="Specific help item chosen within the type of need.")
    pueblo: str = Field(..., description="Town or city where the user is located.")

class PubSubTool(BaseTool):
    name: str = "pubsub_tool"
    description: str = (
        "Use this tool to publish an emergency event to Pub/Sub. "
        "You must provide the chat ID,the name, the type of need, the specific need and the town."
    )
    args_schema: Type[BaseModel] = PubSubPayload

    def _run(self,nombre: str,tipo_necesidad: str,necesidad_especifica: str,pueblo: str) -> str:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.geocode(pueblo)
        datos = {
            "id": "696727663",
            "name": nombre,
            "contact": "632826643",     
            "necessity": tipo_necesidad,
            "specific_need": necesidad_especifica,
            "urgency": 5,
            "city": pueblo,
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "retry_count": 0,
            "is_auto_generated": False,
        }

        data_str = json.dumps(datos, ensure_ascii=False)

        topic_name = "projects/edem24-25/topics/tohelp_topic"

        publisher = pubsub_v1.PublisherClient()
        future = publisher.publish(topic_name, data=data_str.encode("utf-8"))
        message_id = future.result()

        return f"Message published with ID: {message_id}"

    async def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("Async not implemented for PubSubTool")