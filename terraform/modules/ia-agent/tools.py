from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from google.cloud import pubsub_v1

class PubSubPayload(BaseModel):
    topic_name: str = Field(..., description="Nombre del topic en Pub/Sub (formato projects/xxx/topics/xxx)")
    user_id: str = Field(..., description="ID del usuario o chat")
    important_data: str = Field(..., description="Dato importante a enviar a Pub/Sub")

class PubSubTool(BaseTool):
    # Se agregan las anotaciones de tipo a los atributos sobrescritos
    name: str = "pubsub_tool"
    description: str = (
        "Usar esta herramienta para publicar un evento en Pub/Sub. "
        "Debes proveer un topic_name y los campos user_id y important_data."
    )
    args_schema: Type[BaseModel] = PubSubPayload

    def _run(self, topic_name: str, user_id: str, important_data: str) -> str:
        publisher = pubsub_v1.PublisherClient()
        data_str = f"User: {user_id}, Data: {important_data}"
        future = publisher.publish(topic_name, data=data_str.encode("utf-8"))
        message_id = future.result()
        return f"Message published with ID: {message_id}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for PubSubTool")