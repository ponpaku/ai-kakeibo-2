"""add category_rules table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'category_rules',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('pattern', sa.String(length=500), nullable=False),
        sa.Column('match_type', sa.Enum('contains', 'regex', name='matchtype'), nullable=False, server_default='contains'),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('ix_category_rules_priority', 'category_rules', ['priority'])
    op.create_index('ix_category_rules_active', 'category_rules', ['is_active'])


def downgrade():
    op.drop_index('ix_category_rules_active', table_name='category_rules')
    op.drop_index('ix_category_rules_priority', table_name='category_rules')
    op.drop_table('category_rules')
    sa.Enum(name='matchtype').drop(op.get_bind(), checkfirst=False)
