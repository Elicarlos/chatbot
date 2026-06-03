from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    instagram_link = Column(String, nullable=True)
    sizes = Column(String, nullable=True)
    category = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StoreConfig(Base):
    __tablename__ = 'store_configs'

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True, nullable=False)
    order_number = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    details = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="ativo", nullable=False)  # "ativo" ou "transbordo"
    last_csat_rate = Column(Integer, nullable=True)  # Nota de 1 a 5
    created_at = Column(DateTime, default=datetime.utcnow)

class InteractionLog(Base):
    __tablename__ = 'interaction_logs'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True, nullable=False)
    message_in = Column(String, nullable=True)
    message_out = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
