"""add product_name to expenses

Revision ID: 001
Revises:
Create Date: 2025-11-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add product_name column to expenses table"""
    # 商品名カラムを追加（最初はnullable=Trueで追加）
    op.add_column('expenses', sa.Column('product_name', sa.String(length=200), nullable=True))

    # 既存データに対して、descriptionの値をproduct_nameにコピー
    # descriptionが空の場合は「商品」という値を設定
    op.execute("""
        UPDATE expenses
        SET product_name = COALESCE(NULLIF(description, ''), '商品')
        WHERE product_name IS NULL
    """)

    # product_nameをnullable=Falseに変更
    op.alter_column('expenses', 'product_name', nullable=False)


def downgrade():
    """Remove product_name column from expenses table"""
    op.drop_column('expenses', 'product_name')
