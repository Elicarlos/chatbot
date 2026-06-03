"""add instagram link to products

Revision ID: 34567890abcd
Revises: 234567890abc
Create Date: 2026-06-03 18:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '34567890abcd'
down_revision = '234567890abc'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Adiciona a coluna instagram_link na tabela products
    op.add_column('products', sa.Column('instagram_link', sa.String(), nullable=True))
    
    # Atualiza os produtos cadastrados com links ficticios do instagram da loja
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_dino/' WHERE name = 'Conjunto Dino'")
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_floral/' WHERE name = 'Vestido Floral'")
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_confort/' WHERE name = 'Tênis Confort'")
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_body/' WHERE name = 'Body Algodão Doce'")
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_laco/' WHERE name = 'Casaco de Lã'")
    op.execute("UPDATE products SET instagram_link = 'https://www.instagram.com/p/C_exemplo_jeans/' WHERE name = 'Calça Jeans Regulável'")

def downgrade() -> None:
    op.drop_column('products', 'instagram_link')
