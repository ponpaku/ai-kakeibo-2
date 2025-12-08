"""Add tax columns to expense_items

Revision ID: 003
Revises: 002_add_category_rules
Create Date: 2025-12-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_tax_columns'
down_revision = '002_add_category_rules'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('expense_items', sa.Column('tax_rate', sa.Numeric(4, 2), nullable=True))
    op.add_column('expense_items', sa.Column('tax_included', sa.Boolean(), nullable=True))
    op.add_column('expense_items', sa.Column('tax_amount', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('expense_items', 'tax_amount')
    op.drop_column('expense_items', 'tax_included')
    op.drop_column('expense_items', 'tax_rate')
