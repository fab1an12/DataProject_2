import base64
import functions_framework
import os  
import requests
import json

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@functions_framework.cloud_event
def send_message(cloud_event):
    data = base64.b64decode(cloud_event.data["message"]["data"])
    msg = json.loads(data)
    match_id = msg.get("match_id")
    affected_name = msg.get("affected_name")
    text = f"Tu ayuda está de camino {affected_name}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": match_id, "text": text})

    return jsonify({"status_code": resp.status_code, "response": resp.json()})
