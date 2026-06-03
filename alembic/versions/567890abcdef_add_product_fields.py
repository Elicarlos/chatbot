"""add product fields

Revision ID: 567890abcdef
Revises: 4567890abcde
Create Date: 2026-06-03 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '567890abcdef'
down_revision = '4567890abcde'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Adiciona colunas sizes, category, gender e image_url na tabela products
    op.add_column('products', sa.Column('sizes', sa.String(), nullable=True))
    op.add_column('products', sa.Column('category', sa.String(), nullable=True))
    op.add_column('products', sa.Column('gender', sa.String(), nullable=True))
    op.add_column('products', sa.Column('image_url', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('products', 'image_url')
    op.drop_column('products', 'gender')
    op.drop_column('products', 'category')
    op.drop_column('products', 'sizes')
