"""initial

Revision ID: 1234567890ab
Revises: 
Create Date: 2026-06-02 09:17:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '1234567890ab'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_phone_number'), 'customers', ['phone_number'], unique=True)

    op.create_table(
        'interaction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('message_in', sa.String(), nullable=True),
        sa.Column('message_out', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interaction_logs_id'), 'interaction_logs', ['id'], unique=False)
    op.create_index(op.f('ix_interaction_logs_phone_number'), 'interaction_logs', ['phone_number'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_interaction_logs_phone_number'), table_name='interaction_logs')
    op.drop_index(op.f('ix_interaction_logs_id'), table_name='interaction_logs')
    op.drop_table('interaction_logs')
    
    op.drop_index(op.f('ix_customers_phone_number'), table_name='customers')
    op.drop_index(op.f('ix_customers_id'), table_name='customers')
    op.drop_table('customers')
