from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from google.cloud import pubsub_v1

class PubSubPayload(BaseModel):
    """Estructura pydantic para publicar en Pub/Sub."""
    topic_name: str = Field(..., description="Nombre completo del topic, e.g. projects/xxx/topics/xxx")
    user_id: str = Field(..., description="ID del usuario o chat")
    important_data: str = Field(..., description="Información recolectada a lo largo de la conversación")

class PubSubTool(BaseTool):
    name = "pubsub_tool"
    description = (
        "Tool para publicar un mensaje en Pub/Sub con los campos user_id, important_data, etc. "
        "Usar esta tool cuando tengas todos los datos necesarios para la tarea final."
    )
    args_schema = PubSubPayload

    def _run(self, topic_name: str, user_id: str, important_data: str):
        publisher = pubsub_v1.PublisherClient()
        data_str = f"User: {user_id}, Data: {important_data}"
        future = publisher.publish(topic_name, data=data_str.encode("utf-8"))
        message_id = future.result()
        return f"Mensaje publicado con ID: {message_id}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not implemented for PubSubTool")