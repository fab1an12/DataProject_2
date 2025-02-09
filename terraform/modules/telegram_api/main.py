# from fastapi import FastAPI, Request
# import os
# import requests
# import logging

# app = FastAPI()

# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# @app.post("/webhook")
# async def webhook(request: Request):
#     data = await request.json()
#     logging.info(data)
    
#     # if "message" in data:
#     #     chat_id = data["message"]["chat"]["id"]
#     #     text = data["message"]["text"]
#     #     # url = f"https://europe-southwest1-{os.environ.get('ENVIRONMENT')}.cloudfunctions.net/run_agent" 
#     #     # response = requests.post(url, json={"chat_id": chat_id, "text": text})
#     #     # return {"forward_status": response.status_code}
    
#     return {"ok": True}

# @app.post("/send_message")
# def send_message(body: dict):
#     chat_id = body.get("chat_id")
#     text = body.get("text")
    
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     response = requests.post(url, json={"chat_id": chat_id, "text": text})
    
#     return {"status_code": response.status_code, "response": response.json()}

from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Hello from Telegram API Flask on Cloud Run!"})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    logging.info(f"Data received: {data}")
    # Procesa el JSON que llega (por ejemplo, lo reenvías a un agente, etc.)
    # De momento, solo devolvemos {"ok": True}
    return jsonify({"ok": True})

@app.route("/send_message", methods=["POST"])
def send_message():

    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    text = body.get("text", "")

    if not TELEGRAM_BOT_TOKEN:
        return jsonify({"error": "No TELEGRAM_BOT_TOKEN provided"}), 400
    if not chat_id:
        return jsonify({"error": "chat_id is required"}), 400

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text})

    return jsonify({"status_code": resp.status_code, "response": resp.json()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)