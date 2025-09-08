"""Add product moderation support

Revision ID: 200_product_moderation
Revises: 002_merchant_subscription
Create Date: 2025-09-03 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '200_product_moderation'
down_revision = '002_merchant_subscription'
branch_labels = None
depends_on = None


def upgrade():
    # 由于SQLite不支持ALTER TYPE，我们只需确保products表存在
    # 状态字段将在应用层处理，数据库中仍使用字符串类型
    pass


def downgrade():
    # 降级操作无需特殊处理
    pass
