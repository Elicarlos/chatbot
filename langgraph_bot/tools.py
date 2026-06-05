import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Product, StoreConfig, Order, Customer
from langchain_core.tools import tool

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@tool
def list_products() -> str:
    """
    Retorna a lista de todos os produtos cadastrados na loja Fluence Store Kids, 
    com o respectivo nome, preço, descrição, tamanho, categoria, gênero e link do Instagram.
    """
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            return "Nenhum produto cadastrado no estoque no momento."
        
        ret = "Aqui está a lista de produtos disponíveis na Fluence Store Kids:\n"
        for p in products:
            link = f" | Link: {p.instagram_link}" if p.instagram_link else ""
            sizes = f" | Tamanhos: {p.sizes}" if p.sizes else ""
            gender = f" | Gênero: {p.gender}" if p.gender else ""
            category = f" | Categoria: {p.category}" if p.category else ""
            ret += f"- {p.name}: R$ {p.price:.2f} ({p.description}{category}{gender}{sizes}{link})\n"
        return ret
    except Exception as e:
        return f"Erro ao acessar o banco de dados para listar produtos: {str(e)}"
    finally:
        db.close()

from sqlalchemy import and_, or_

@tool
def get_product_details(name: str) -> str:
    """
    Busca o preço, descrição, estoque, tamanhos, categoria, gênero, foto e link do Instagram de produtos na loja Fluence Store Kids 
    a partir de um ou mais termos de busca (ex: "vestido 6" ou "conjunto feminino"). A busca analisa nome, descrição, categoria e tamanhos.
    """
    db = SessionLocal()
    try:
        # Quebra o termo de busca em palavras e remove termos de ruído (stopwords)
        stopwords = {
            'de', 'para', 'com', 'em', 'um', 'uma', 'os', 'as', 'o', 'a', 
            'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'tamanho', 
            'tamanhos', 'ano', 'anos', 'mes', 'meses', 'idade', 'idades', 
            'peças', 'pecas', 'infantil', 'bebe', 'bebê', 'criança', 'crianca',
            'loja', 'disponivel', 'disponíveis', 'tem', 'temos', 'voce', 'você'
        }
        raw_words = [w.strip().lower() for w in name.split() if w.strip()]
        words = [w for w in raw_words if w not in stopwords]
        
        # Se após a limpeza não sobrar nada (ex: buscaram apenas por "anos"), usamos a busca original
        if not words:
            words = raw_words
            
        if not words:
            return f"Não encontrei nenhum produto correspondente a '{name}'."
        
        # Constrói os filtros: cada palavra buscada deve estar presente em pelo menos um dos campos do produto
        conditions = []
        for word in words:
            conditions.append(
                or_(
                    Product.name.ilike(f"%{word}%"),
                    Product.description.ilike(f"%{word}%"),
                    Product.category.ilike(f"%{word}%"),
                    Product.sizes.ilike(f"%{word}%")
                )
            )
        
        # Executa a busca exigindo que todas as palavras-chave sejam satisfeitas
        products = db.query(Product).filter(and_(*conditions)).all()
        
        if not products:
            return f"Não encontrei nenhum produto correspondente a '{name}'."
        
        ret = "Encontrei o(s) seguinte(s) produto(s):\n"
        for product in products:
            link = f"\nLink do Instagram: {product.instagram_link}" if product.instagram_link else ""
            sizes = f"\nTamanhos Disponíveis: {product.sizes}" if product.sizes else ""
            gender = f"\nPúblico (Gênero): {product.gender}" if product.gender else ""
            category = f"\nCategoria: {product.category}" if product.category else ""
            image = f"\nFoto do Produto: {product.image_url}" if product.image_url else ""
            ret += (
                f"\n- Produto: {product.name}\n"
                f"  Preço: R$ {product.price:.2f}\n"
                f"  Descrição: {product.description}\n"
                f"  Estoque: {product.stock} unidades disponíveis."
                f"{category}{gender}{sizes}{link}{image}\n"
            )
        return ret
    except Exception as e:
        return f"Erro ao acessar o banco de dados para buscar o produto: {str(e)}"
    finally:
        db.close()


@tool
def get_store_info(key: str) -> str:
    """
    Consulta informações institucionais sobre a loja Fluence Store Kids.
    Use este comando com as chaves:
    - 'horario_funcionamento' (para consultar o horário de atendimento)
    - 'dados_pix' (para informações sobre pagamentos via Pix)
    - 'endereco' (para localização física)
    - 'formas_pagamento' (para cartões de crédito e outras formas de pagamento)
    """
    db = SessionLocal()
    try:
        config = db.query(StoreConfig).filter(StoreConfig.key == key).first()
        if not config:
            return f"Não encontrei informações cadastradas para a chave '{key}'."
        return f"Informação sobre {key}: {config.value}"
    except Exception as e:
        return f"Erro ao consultar dados da loja: {str(e)}"
    finally:
        db.close()

@tool
def check_order_status(phone_number: str, order_number: str) -> str:
    """
    Verifica o status de entrega e detalhes de um pedido específico do cliente
    pelo número de telefone (JID do remetente) e número do pedido (ex: 'FS1002').
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.phone_number == phone_number,
            Order.order_number.ilike(order_number.strip())
        ).first()
        if not order:
            return f"Não encontrei nenhum pedido com o número '{order_number}' associado ao seu número de telefone."
        
        return (
            f"Pedido: {order.order_number}\n"
            f"Status Atual: {order.status}\n"
            f"Detalhes: {order.details}\n"
            f"Última Atualização: {order.updated_at.strftime('%d/%m/%Y %H:%M') if order.updated_at else 'Sem registro'}"
        )
    except Exception as e:
        return f"Erro ao consultar o status do pedido: {str(e)}"
    finally:
        db.close()

@tool
def transferir_atendimento_humano(phone_number: str) -> str:
    """
    Transfere e pausa o atendimento do chatbot, marcando o cliente no banco de dados como
    em transbordo humano ('transbordo') para que o suporte humano possa interagir diretamente pelo WhatsApp.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.phone_number == phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number, status="transbordo")
            db.add(customer)
        else:
            customer.status = "transbordo"
        db.commit()
        return "Atendimento transferido para o suporte humano com sucesso. As respostas automáticas do robô foram pausadas."
    except Exception as e:
        return f"Erro ao solicitar transferência de atendimento: {str(e)}"
    finally:
        db.close()

@tool
def registrar_avaliacao_csat(phone_number: str, nota: int) -> str:
    """
    Registra a avaliação de satisfação do cliente (nota de 1 a 5) no banco de dados.
    Utilize quando o cliente fornecer explicitamente a nota de avaliação no final da conversa.
    """
    if nota < 1 or nota > 5:
        return "A nota de avaliação deve ser um número inteiro de 1 a 5."
        
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.phone_number == phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number, last_csat_rate=nota)
            db.add(customer)
        else:
            customer.last_csat_rate = nota
        db.commit()
        return f"Nota de atendimento {nota} registrada com sucesso. Agradecemos muito pelo feedback!"
    except Exception as e:
        return f"Erro ao registrar avaliação de satisfação: {str(e)}"
    finally:
        db.close()

