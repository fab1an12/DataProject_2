import os
import requests
import logging
from flask import Flask, request, jsonify
from google.cloud import firestore
from langchain import hub
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tools import PubSubTool

TELEGRAM_URL = os.environ.get("TELEGRAM_URL")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

prompt = hub.pull("hwchase17/structured-chat-agent")

def build_agent(memory: ConversationBufferMemory) -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    tool_pubsub = PubSubTool()
    tools = [tool_pubsub]

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
    if len(memory.chat_memory.messages) == 0:
        initial_message = (
            "Eres un asistente que sigue estas directrices:\n"
            "- Respetas el prompt.\n"
            "- Usas las herramientas solo cuando sea necesario.\n"
            "- Recopilas variables y, al final, usas 'pubsub_tool'.\n"
            "..."
        )
        memory.chat_memory.add_message(SystemMessage(content=initial_message))
    return agent_executor

@app.route("/run_agent", methods=["POST"])
def run_agent_endpoint():
    body = request.get_json(silent=True) or {}
    logging.info(f"Data received: {body}")
    chat_id = body.get("chat_id")
    user_message = body.get("text", "")
    if not chat_id:
        return jsonify({"error": "chat_id is required"}), 400

    db = firestore.Client()
    doc_ref = db.collection("chat_sessions").document(str(chat_id))
    doc = doc_ref.get()
    messages = []
    if doc.exists:
        data = doc.to_dict()
        messages = data.get("messages", [])
        logging.info(f"Loaded {len(messages)} messages for session {chat_id} from Firestore")
    else:
        logging.info(f"No previous session for {chat_id}. Starting fresh.")

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    for msg in messages:
        if msg.get("type") == "human":
            memory.chat_memory.add_message(HumanMessage(content=msg.get("content")))
        elif msg.get("type") == "ai":
            memory.chat_memory.add_message(AIMessage(content=msg.get("content")))

    agent_executor = build_agent(memory)
    response = agent_executor.invoke({"input": user_message})
    agent_reply = response.get("output", "")

    serialized = []
    for m in memory.chat_memory.messages:
        if isinstance(m, HumanMessage):
            serialized.append({"type": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serialized.append({"type": "ai", "content": m.content})
    doc_ref.set({"messages": serialized})
    logging.info(f"Saved {len(serialized)} messages for session {chat_id} to Firestore")

    bridge_endpoint = TELEGRAM_URL.rstrip("/") + "/send_message"
    payload = {
        "chat_id": chat_id,
        "text": agent_reply
    }
    try:
        requests.post(bridge_endpoint, json=payload)
    except Exception as e:
        logging.error(f"Error sending message to bridge: {e}")
        return jsonify({
            "error": f"Error sending message to bridge: {str(e)}",
            "agent_reply": agent_reply
        }), 500

    return jsonify({"reply": agent_reply})

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "LangChain Agent (React) en Cloud Run con Flask - Memory inline"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)