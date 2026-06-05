import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Carrega as variáveis do .env local
load_dotenv()

# Configura banco de dados SQLite temporário em memória nas variáveis de ambiente
# antes de importar os módulos do projeto para evitar erros de inicialização.
DATABASE_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = DATABASE_URL

# Cria o engine do teste
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configura o mock do banco em tools e models
import models
models.DATABASE_URL = DATABASE_URL
models.engine = engine
models.SessionLocal = SessionLocal

import langgraph_bot.tools
langgraph_bot.tools.SessionLocal = SessionLocal


from models import Base, Product, Customer
from langgraph_bot.agent import process_message_with_ai

def setup_mock_db():
    # Cria as tabelas na memória
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # Adiciona produto de teste correspondente ao seu catálogo
    vestido = Product(
        name="Vestido",
        description="Vestido rosa",
        price=100.00,
        stock=5,
        sizes="6, 8, 10",
        instagram_link="https://www.instagram.com/p/C0M8Ll9PVhL/?img_index=1"
    )
    db.add(vestido)
    
    # Cadastra o cliente de teste
    cliente = Customer(
        phone_number="teste_local",
        name="Elicarlos",
        status="ativo"
    )
    db.add(cliente)
    db.commit()
    db.close()

def main():
    print("====================================================")
    print(" INICIANDO TESTE DO CHATBOT LOCAL (CONSOLE)")
    print("====================================================")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or "substitua" in groq_key:
        print("Erro: Chave GROQ_API_KEY não configurada ou inválida no seu arquivo .env local.")
        sys.exit(1)
        
    print("Criando banco de dados temporário em memória (SQLite)...")
    setup_mock_db()
    print("Banco de dados configurado com o produto 'Vestido' (tamanhos 6, 8, 10).")
    print("Pronto para conversar! Digite 'sair' para encerrar.\n")
    
    user_id = "teste_local"
    customer_name = "Elicarlos"
    
    while True:
        try:
            mensagem = input("\nVocê: ")
            if mensagem.strip().lower() == 'sair':
                break
                
            if not mensagem.strip():
                continue
                
            print("Processando resposta da IA (Groq)...")
            resposta = process_message_with_ai(user_id, mensagem, customer_name=customer_name)
            print(f"\nBot: {resposta}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nErro no processamento: {str(e)}")

if __name__ == "__main__":
    main()
