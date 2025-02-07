from fastapi import FastAPI, Request
import os
import requests
import logging

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logging.info(data)
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        url = f"https://europe-southwest1-{os.environ.get('ENVIRONMENT')}.cloudfunctions.net/run_agent" 
        response = requests.post(url, json={"chat_id": chat_id, "text": text})
        return {"forward_status": response.status_code}
    
    return {"ok": True}

@app.post("/send_message")
def send_message(body: dict):
    chat_id = body.get("chat_id")
    text = body.get("text")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": text})
    
    return {"status_code": response.status_code, "response": response.json()}
