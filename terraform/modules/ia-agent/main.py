import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from google.cloud import firestore
from google.cloud import pubsub_v1

from langchain.callbacks import tracing
from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.llms import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from memory import get_conversation_memory
from tools import PubSubTool

os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.environ.get("LANGCHAIN_API_KEY")

app = FastAPI()

prompt = hub.pull("hwchase17/structured-chat-agent")

def build_agent(session_id: str):
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    tool_pubsub = PubSubTool()
    tools = [tool_pubsub]

    memory = get_conversation_memory(session_id=session_id)

    agent = create_structured_chat_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True
    )

    initial_message = (
        "Eres un asistente que sigue estas directrices:\n"
        "- Respetas el prompt.\n"
        "- Usas las herramientas sólo cuando sea necesario.\n"
        "- Recopilas variables y al final usas 'pubsub_tool'.\n"
        "..."
    )
    # Añadimos ese mensaje a la memoria (SystemMessage) si es la 1ª vez
    if len(memory.chat_memory.messages) == 0:
        memory.chat_memory.add_message(SystemMessage(content=initial_message))

    return agent_executor

@app.post("/run_agent")
async def run_agent_endpoint(req: Request):
    """
    Endpoint que recibe un JSON como:
    {
      "chat_id": "...",
      "message": "Mensaje del usuario"
    }
    y devuelve la respuesta del agente.

    Luego reenvía esa respuesta al endpoint /send_message
    de la función puente para que llegue a Telegram.
    """
    data = await req.json()
    chat_id = data.get("chat_id")
    user_message = data.get("message", "")

    if not chat_id or not user_message:
        return JSONResponse({"error": "Faltan campos chat_id o message"}, status_code=400)

    # Construir/obtener agente
    agent_executor = build_agent(session_id=str(chat_id))

    # Añadir el mensaje del usuario a la memoria
    memory = agent_executor.memory
    memory.chat_memory.add_message(HumanMessage(content=user_message))

    # Ejecutar dentro de un bloque de tracing (para LangSmith)
    with tracing("gcf-agent-invocation"):
        response = agent_executor.invoke({"input": user_message})

    # Agregar respuesta del agente a la memoria
    agent_reply = response["output"]
    memory.chat_memory.add_message(AIMessage(content=agent_reply))

    # Enviar la respuesta del agente a la función puente, para que llegue a Telegram
    bridge_endpoint = f"https://europe-southwest1-{os.environ.get('ENVIRONMENT')}.cloudfunctions.net/send_message"
    payload = {
            "chat_id": chat_id,
            "text": agent_reply
    }
    try:
        resp = requests.post(bridge_endpoint, json=payload)
        resp.raise_for_status()
    except Exception as e:
        return JSONResponse(
            content={
                "error": f"Error enviando el mensaje al bridge: {str(e)}", 
                "agent_reply": agent_reply
            },
            status_code=500
        )

    # Opcionalmente, devolvemos la respuesta del agente
    return {"reply": agent_reply}

# (Opcional) root, para prueba rápida
@app.get("/")
def root():
    return {"message": "LangChain Agent (React) en Cloud Function con FastAPI"}