"""add store features

Revision ID: 4567890abcde
Revises: 34567890abcd
Create Date: 2026-06-03 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = '4567890abcde'
down_revision = '34567890abcd'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Cria a tabela store_configs
    op.create_table(
        'store_configs',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    op.create_index(op.f('ix_store_configs_key'), 'store_configs', ['key'], unique=False)

    # 2. Cria a tabela orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('order_number', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('details', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_phone_number'), 'orders', ['phone_number'], unique=False)

    # 3. Adiciona colunas status e last_csat_rate na tabela customers
    op.add_column('customers', sa.Column('status', sa.String(), server_default='ativo', nullable=False))
    op.add_column('customers', sa.Column('last_csat_rate', sa.Integer(), nullable=True))

    # 4. Popula sementes (seed data) para store_configs
    store_configs_table = table(
        'store_configs',
        column('key', sa.String),
        column('value', sa.String)
    )
    op.bulk_insert(
        store_configs_table,
        [
            {"key": "horario_funcionamento", "value": "Segunda a Sexta das 08:00 às 18:00, e Sábado das 08:00 às 12:00."},
            {"key": "dados_pix", "value": "Chave CNPJ: 12.345.678/0001-99 - Fluence Store Kids LTDA."},
            {"key": "endereco", "value": "Av. Dom Severino, 1000 - Bairro Fátima, Teresina - PI, CEP 64049-375."},
            {"key": "formas_pagamento", "value": "Pix (com 5% de desconto), Cartão de Crédito/Débito (Visa, Mastercard, Elo) ou Boleto."}
        ]
    )

    # 5. Popula sementes (seed data) de teste para orders
    orders_table = table(
        'orders',
        column('phone_number', sa.String),
        column('order_number', sa.String),
        column('status', sa.String),
        column('details', sa.String)
    )
    op.bulk_insert(
        orders_table,
        [
            {
                "phone_number": "5586999998888@s.whatsapp.net",
                "order_number": "FS1002",
                "status": "Em trânsito",
                "details": "1x Vestido Floral tamanho 6. O pedido saiu para entrega hoje pela manhã."
            },
            {
                "phone_number": "5586999998888@s.whatsapp.net",
                "order_number": "FS1003",
                "status": "Entregue",
                "details": "1x Tênis Confort tamanho 28. Entregue no dia 02/06/2026."
            }
        ]
    )

def downgrade() -> None:
    # Remove as colunas adicionadas na tabela customers
    op.drop_column('customers', 'last_csat_rate')
    op.drop_column('customers', 'status')

    # Remove a tabela orders
    op.drop_index(op.f('ix_orders_phone_number'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_number'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')

    # Remove a tabela store_configs
    op.drop_index(op.f('ix_store_configs_key'), table_name='store_configs')
    op.drop_table('store_configs')
