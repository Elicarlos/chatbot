import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Product
from langchain_core.tools import tool

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@tool
def list_products() -> str:
    """
    Retorna a lista de todos os produtos cadastrados na loja Fluence Store Kids, 
    com o respectivo nome, preço e descrição.
    """
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            return "Nenhum produto cadastrado no estoque no momento."
        
        ret = "Aqui está a lista de produtos disponíveis na Fluence Store Kids:\n"
        for p in products:
            ret += f"- {p.name}: R$ {p.price:.2f} ({p.description})\n"
        return ret
    except Exception as e:
        return f"Erro ao acessar o banco de dados para listar produtos: {str(e)}"
    finally:
        db.close()

@tool
def get_product_details(name: str) -> str:
    """
    Busca o preço, descrição e estoque de um produto específico na loja Fluence Store Kids 
    pelo nome (permite buscas parciais).
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.name.ilike(f"%{name}%")).first()
        if not product:
            return f"Não encontrei nenhum produto correspondente a '{name}'."
        
        return (
            f"Produto: {product.name}\n"
            f"Preço: R$ {product.price:.2f}\n"
            f"Descrição: {product.description}\n"
            f"Estoque: {product.stock} unidades disponíveis."
        )
    except Exception as e:
        return f"Erro ao acessar o banco de dados para buscar o produto: {str(e)}"
    finally:
        db.close()

