# memory_manager.py

from langchain.memory import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from langchain.schema import AIMessage, HumanMessage
from google.cloud import firestore

class FirestoreChatMessageHistory(ChatMessageHistory):
    """
    Implementación personalizada para guardar la conversación en Firestore
    basada en un session_id (por ejemplo, el chat_id de Telegram).
    """
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id
        self.db = firestore.Client()
        self.collection = self.db.collection("chat_sessions")
        self.load_messages()

    def load_messages(self):
        doc = self.collection.document(self.session_id).get()
        if doc.exists:
            data = doc.to_dict()
            stored_messages = data.get("messages", [])
            for msg in stored_messages:
                if msg["type"] == "human":
                    self.messages.append(HumanMessage(content=msg["content"]))
                else:
                    self.messages.append(AIMessage(content=msg["content"]))

    def save_messages(self):
        # Serializamos el historial
        serialized = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                serialized.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                serialized.append({"type": "ai", "content": msg.content})

        self.collection.document(self.session_id).set({"messages": serialized})

    def add_user_message(self, message: str) -> None:
        super().add_user_message(message)
        self.save_messages()

    def add_ai_message(self, message: str) -> None:
        super().add_ai_message(message)
        self.save_messages()

def get_conversation_memory(session_id: str) -> ConversationBufferMemory:
    chat_history = FirestoreChatMessageHistory(session_id=session_id)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=chat_history
    )
    return memory