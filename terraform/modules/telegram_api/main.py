from flask import Flask, request, jsonify
import os
import requests
import logging

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AGENT_URL = os.environ.get("AGENT_URL")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    logging.info(f"Data received: {data}")
    
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]
    url = AGENT_URL.rstrip("/") + "/run_agent"
    requests.post(url, json={"chat_id": chat_id, "text": text})
    logging.info(f"Message sent to agent at {url}")
    return jsonify({"status": "ok"})

@app.route("/send_message", methods=["POST"])
def send_message():

    body = request.get_json(silent=True) or {}
    chat_id = body.get("chat_id")
    text = body.get("text", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text})

    return jsonify({"status_code": resp.status_code, "response": resp.json()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)