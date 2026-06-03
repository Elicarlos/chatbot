import os
import logging
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot Webhook API")

# Protege o webhook contra ataques externos
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

class WebhookPayload(BaseModel):
    event: str
    data: dict

@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(
    payload: WebhookPayload,
    authorization: str = Header(None)
):
    # Verificacao de seguranca do webhook (Impede acesso nao autorizado)
    if authorization != f"Bearer {WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    event_type = payload.event
    
    # Processa mensagens de entrada
    if event_type == "messages.upsert":
        messages = payload.data.get("messages", [])
        for msg in messages:
            # Ignora mensagens geradas pelo proprio bot
            if msg.get("key", {}).get("fromMe"):
                continue
            
            sender = msg.get("key", {}).get("remoteJid")
            text = msg.get("message", {}).get("conversation")
            
            logger.info(f"Nova mensagem segura recebida de {sender}: {text}")
            
    return {"status": "received"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
