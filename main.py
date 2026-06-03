import os
import logging
import requests
from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Customer, InteractionLog
from langgraph_bot.agent import process_message_with_ai

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot Webhook API")

# Protege o webhook contra ataques externos
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Configuração de conexão do banco de dados para salvar interações
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def extract_message_text(data: dict) -> str:
    """
    Extrai o conteúdo textual de mensagens de forma flexível a partir do
    payload enviado pela Evolution API.
    """
    message = data.get("message", {})
    if not message:
        return ""
    
    # Mensagem de texto simples
    if "conversation" in message:
        return message["conversation"]
    
    # Mensagem de texto estendida
    if "extendedTextMessage" in message:
        return message["extendedTextMessage"].get("text", "")
        
    # Imagem com legenda
    if "imageMessage" in message:
        return message["imageMessage"].get("caption", "")
        
    # Vídeo com legenda
    if "videoMessage" in message:
        return message["videoMessage"].get("caption", "")
        
    return ""

def send_whatsapp_message(instance: str, to_number: str, text: str):
    """
    Envia uma mensagem de texto de volta utilizando a Evolution API.
    """
    api_url = os.getenv("EVOLUTION_API_URL", "http://evolution-api:8080")
    api_key = os.getenv("EVOLUTION_API_KEY")
    
    url = f"{api_url}/message/sendText/{instance}"
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key
    }
    payload = {
        "number": to_number,
        "text": text
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Mensagem enviada com sucesso para {to_number} na instância {instance}")
    except Exception as e:
        logger.error(f"Erro ao enviar resposta via Evolution API: {str(e)}")

@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(
    payload: dict,
    authorization: str = Header(None)
):
    # Verificação de segurança do webhook (Impede acesso não autorizado)
    if authorization != f"Bearer {WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    event_type = payload.get("event")
    instance = payload.get("instance")
    
    # Processa mensagens de entrada
    if event_type == "messages.upsert":
        data = payload.get("data", {})
        if not data:
            return {"status": "empty_data"}
            
        key = data.get("key", {})
        # Ignora mensagens geradas pelo próprio bot
        if key.get("fromMe"):
            return {"status": "ignored_self"}
            
        sender = key.get("remoteJid")
        text = extract_message_text(data)
        
        if not text:
            return {"status": "no_text_to_process"}
            
        logger.info(f"Mensagem recebida de {sender} na instância {instance}: {text}")
        
        # 1. Processa a mensagem usando o agente inteligente e cordial
        response_text = process_message_with_ai(sender, text)
        
        # 2. Salva o cliente e o log da interação no banco de dados local
        db = SessionLocal()
        try:
            # Verifica se o cliente já está cadastrado
            customer = db.query(Customer).filter(Customer.phone_number == sender).first()
            if not customer:
                push_name = data.get("pushName")
                customer = Customer(phone_number=sender, name=push_name)
                db.add(customer)
            
            # Registra o histórico da mensagem
            interaction = InteractionLog(
                phone_number=sender,
                message_in=text,
                message_out=response_text
            )
            db.add(interaction)
            db.commit()
        except Exception as db_err:
            logger.error(f"Erro ao gerenciar dados no banco local: {str(db_err)}")
            db.rollback()
        finally:
            db.close()
            
        # 3. Envia a resposta de volta ao WhatsApp
        send_whatsapp_message(instance, sender, response_text)
        
    return {"status": "processed"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

