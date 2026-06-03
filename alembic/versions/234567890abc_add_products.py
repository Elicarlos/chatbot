"""add products

Revision ID: 234567890abc
Revises: 1234567890ab
Create Date: 2026-06-03 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = '234567890abc'
down_revision = '1234567890ab'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Cria a tabela de produtos
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=True)

    # Popula a tabela com produtos iniciais da Fluence Store Kids
    products_table = table(
        'products',
        column('name', sa.String),
        column('description', sa.String),
        column('price', sa.Numeric),
        column('stock', sa.Integer)
    )

    op.bulk_insert(
        products_table,
        [
            {
                "name": "Conjunto Dino",
                "description": "Conjunto de moletom infantil com capuz e estampa de dinossauro. Super quentinho e confortável.",
                "price": 89.90,
                "stock": 15
            },
            {
                "name": "Vestido Floral",
                "description": "Vestido infantil floral em algodão leve, perfeito para dias ensolarados e passeios.",
                "price": 79.90,
                "stock": 10
            },
            {
                "name": "Tênis Confort",
                "description": "Tênis infantil slip-on com sola flexível e antiderrapante, ideal para o dia a dia escolar.",
                "price": 119.90,
                "stock": 20
            },
            {
                "name": "Body Algodão Doce",
                "description": "Body para bebê manga longa em algodão egípcio, hipoalergênico e macio.",
                "price": 39.90,
                "stock": 35
            },
            {
                "name": "Casaco de Lã",
                "description": "Casaco infantil de lã batida forrado, com fechamento em botões elegantes.",
                "price": 129.90,
                "stock": 8
            },
            {
                "name": "Calça Jeans Regulável",
                "description": "Calça jeans infantil clássica com ajuste interno de elástico na cintura.",
                "price": 69.90,
                "stock": 25
            }
        ]
    )

def downgrade() -> None:
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
