import os
import logging
import requests
import secrets
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from models import Customer, InteractionLog, Product
from langgraph_bot.agent import process_message_with_ai

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot Webhook API")

# Protege o webhook contra ataques externos
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Pydantic schemas para o painel de administracao
class ProductSchema(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int = 0
    instagram_link: str | None = None
    sizes: str | None = None
    category: str | None = None
    gender: str | None = None
    image_url: str | None = None

class StatusSchema(BaseModel):
    status: str


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
        
        db = SessionLocal()
        try:
            # 1. Verifica ou cadastra o cliente
            customer = db.query(Customer).filter(Customer.phone_number == sender).first()
            if not customer:
                push_name = data.get("pushName")
                customer = Customer(phone_number=sender, name=push_name, status="ativo")
                db.add(customer)
                db.commit()
                db.refresh(customer)
                
            # 2. Verifica se o atendimento está em modo suporte humano (transbordo)
            is_transbordo = customer.status == "transbordo"
            if is_transbordo:
                # Permite que o cliente volte ao atendimento do bot usando a palavra-chave #voltar
                if text.strip().lower() == "#voltar":
                    customer.status = "ativo"
                    db.commit()
                    logger.info(f"Cliente {sender} reativou o atendimento do chatbot.")
                    is_transbordo = False
                else:
                    logger.info(f"Mensagem de {sender} ignorada: chatbot pausado (suporte humano ativo).")
                    db.close()
                    return {"status": "transbordo_active_ignored"}
            
            # Fecha a conexão do banco antes de chamar a API da OpenAI para evitar esgotamento de pool e Gateway Timeout
            db.close()
            
            # 3. Processa a mensagem usando o agente inteligente e cordial
            response_text = process_message_with_ai(sender, text)
            
            # 4. Registra o histórico da mensagem abrindo uma nova conexão rápida
            db = SessionLocal()
            interaction = InteractionLog(
                phone_number=sender,
                message_in=text,
                message_out=response_text
            )
            db.add(interaction)
            db.commit()
            
            # 5. Envia a resposta de volta ao WhatsApp
            send_whatsapp_message(instance, sender, response_text)
            
        except Exception as err:
            logger.error(f"Erro no processamento do fluxo de atendimento: {str(err)}")
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
        
    return {"status": "processed"}

# ----------------- SEGURANÇA E AUTENTICAÇÃO DO PAINEL -----------------

security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "fluence_store_kids_2026")

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = ADMIN_USER.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = ADMIN_PASSWORD.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ----------------- ROTAS DO PAINEL ADMIN -----------------

@app.get("/admin", response_class=HTMLResponse)
def get_admin_dashboard(username: str = Depends(authenticate_admin)):
    try:
        with open("admin.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(content=f"<h3>Erro ao carregar o painel administrativo: {str(e)}</h3>", status_code=500)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("favicon.ico")

@app.get("/favicon-96x96.png", include_in_schema=False)
def favicon_96():
    return FileResponse("favicon-96x96.png")

@app.get("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon():
    return FileResponse("apple-touch-icon.png")

@app.get("/web-app-manifest-192x192.png", include_in_schema=False)
def manifest_192():
    return FileResponse("web-app-manifest-192x192.png")

@app.get("/web-app-manifest-512x512.png", include_in_schema=False)
def manifest_512():
    return FileResponse("web-app-manifest-512x512.png")

@app.get("/site.webmanifest", include_in_schema=False)
def webmanifest():
    return FileResponse("site.webmanifest")

@app.get("/api/admin/metrics")
def get_metrics(username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        total_clientes = db.query(Customer).count()
        total_interacoes = db.query(InteractionLog).count()
        
        # Nota média CSAT
        avg_csat = db.query(func.avg(Customer.last_csat_rate)).filter(Customer.last_csat_rate != None).scalar()
        avg_csat = float(avg_csat) if avg_csat else 0.0
        
        # Horários de pico
        logs = db.query(InteractionLog.created_at).all()
        horas_pico = [0] * 24
        for log in logs:
            if log.created_at:
                horas_pico[log.created_at.hour] += 1
                
        # Status de Transbordo
        transbordos = db.query(Customer).filter(Customer.status == "transbordo").count()
        
        return {
            "total_clientes": total_clientes,
            "total_interacoes": total_interacoes,
            "media_csat": round(avg_csat, 2),
            "total_transbordo": transbordos,
            "horas_pico": horas_pico
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/admin/customers")
def get_customers(username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
        return [
            {
                "id": c.id,
                "phone_number": c.phone_number,
                "name": c.name or "Sem Nome",
                "status": c.status,
                "last_csat_rate": c.last_csat_rate,
                "created_at": c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else None
            }
            for c in customers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/admin/customers/{phone_number}/status")
def update_customer_status(phone_number: str, schema: StatusSchema, username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        # Decodifica se houver caracteres especiais na URL (geralmente nao ha no JID)
        customer = db.query(Customer).filter(Customer.phone_number == phone_number).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        if schema.status not in ["ativo", "transbordo"]:
            raise HTTPException(status_code=400, detail="Status inválido")
            
        customer.status = schema.status
        db.commit()
        return {"status": "success", "new_status": customer.status}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/admin/customers/{phone_number}/logs")
def get_customer_logs(phone_number: str, username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        logs = db.query(InteractionLog).filter(InteractionLog.phone_number == phone_number).order_by(InteractionLog.created_at.asc()).all()
        return [
            {
                "id": l.id,
                "message_in": l.message_in,
                "message_out": l.message_out,
                "created_at": l.created_at.strftime("%d/%m/%Y %H:%M:%S") if l.created_at else None
            }
            for l in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/admin/products")
def get_products(username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.name.asc()).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": float(p.price),
                "stock": p.stock,
                "instagram_link": p.instagram_link,
                "sizes": p.sizes,
                "category": p.category,
                "gender": p.gender,
                "image_url": p.image_url
            }
            for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/admin/products")
def create_product(product: ProductSchema, username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        # Verifica se já existe
        exists = db.query(Product).filter(Product.name.ilike(product.name.strip())).first()
        if exists:
            raise HTTPException(status_code=400, detail="Já existe um produto com este nome")
            
        new_prod = Product(
            name=product.name.strip(),
            description=product.description,
            price=product.price,
            stock=product.stock,
            instagram_link=product.instagram_link,
            sizes=product.sizes,
            category=product.category,
            gender=product.gender,
            image_url=product.image_url
        )
        db.add(new_prod)
        db.commit()
        db.refresh(new_prod)
        return {"status": "success", "product_id": new_prod.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.put("/api/admin/products/{product_id}")
def update_product(product_id: int, product: ProductSchema, username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        prod = db.query(Product).filter(Product.id == product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
            
        prod.name = product.name.strip()
        prod.description = product.description
        prod.price = product.price
        prod.stock = product.stock
        prod.instagram_link = product.instagram_link
        prod.sizes = product.sizes
        prod.category = product.category
        prod.gender = product.gender
        prod.image_url = product.image_url
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, username: str = Depends(authenticate_admin)):
    db = SessionLocal()
    try:
        prod = db.query(Product).filter(Product.id == product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
            
        db.delete(prod)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

