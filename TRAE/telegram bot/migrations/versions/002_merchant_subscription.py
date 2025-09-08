"""Add merchant subscription and promotion features

Revision ID: 002_merchant_subscription
Revises: 001_b2c_platform_transformation
Create Date: 2025-08-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_merchant_subscription'
down_revision = '001_b2c_platform'
branch_labels = None
depends_on = None


def upgrade():
    """添加商家订阅和推广功能"""
    
    # 1. 为merchants表添加订阅相关字段
    op.add_column('merchants', sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free', comment='订阅等级: free, professional, enterprise'))
    op.add_column('merchants', sa.Column('subscription_expires_at', sa.TIMESTAMP(timezone=True), nullable=True, comment='订阅到期时间，null表示永久或未订阅'))
    op.add_column('merchants', sa.Column('subscription_auto_renew', sa.Boolean, nullable=False, server_default='false', comment='是否自动续费'))
    
    # 2. 为products表的sort_order添加注释，明确用途
    op.alter_column('products', 'sort_order', comment='用于付费置顶的排序权重，值越小越靠前，0为正常排序')
    
    # 3. 创建商家订阅历史表
    op.create_table('merchant_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False, comment='订阅记录ID'),
        sa.Column('merchant_id', sa.Integer(), nullable=False, comment='商家ID'),
        sa.Column('tier', sa.String(50), nullable=False, comment='订阅等级'),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True), nullable=False, comment='订阅开始时间'),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True), nullable=False, comment='订阅结束时间'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='订阅费用'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='CNY', comment='货币'),
        sa.Column('payment_method', sa.String(50), nullable=True, comment='支付方式'),
        sa.Column('payment_status', sa.String(20), nullable=False, server_default='pending', comment='支付状态: pending, paid, failed, refunded'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='商家订阅历史记录'
    )
    op.create_index('ix_merchant_subscriptions_merchant_id', 'merchant_subscriptions', ['merchant_id'])
    op.create_index('ix_merchant_subscriptions_tier', 'merchant_subscriptions', ['tier'])
    op.create_index('ix_merchant_subscriptions_dates', 'merchant_subscriptions', ['start_date', 'end_date'])
    
    # 4. 创建置顶推广订单表
    op.create_table('promotion_orders',
        sa.Column('id', sa.Integer(), nullable=False, comment='推广订单ID'),
        sa.Column('merchant_id', sa.Integer(), nullable=False, comment='商家ID'),
        sa.Column('product_id', sa.Integer(), nullable=True, comment='商品ID，null表示推广整个商家'),
        sa.Column('promotion_type', sa.String(20), nullable=False, comment='推广类型: top_listing, featured'),
        sa.Column('target_region_id', sa.Integer(), nullable=True, comment='目标推广地区'),
        sa.Column('sort_weight', sa.Integer(), nullable=False, server_default='100', comment='排序权重，值越小越靠前'),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True), nullable=False, comment='推广开始时间'),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True), nullable=False, comment='推广结束时间'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='推广费用'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='CNY', comment='货币'),
        sa.Column('payment_status', sa.String(20), nullable=False, server_default='pending', comment='支付状态'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active', comment='推广状态: active, paused, completed, cancelled'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_region_id'], ['regions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='商家置顶推广订单'
    )
    op.create_index('ix_promotion_orders_merchant_id', 'promotion_orders', ['merchant_id'])
    op.create_index('ix_promotion_orders_product_id', 'promotion_orders', ['product_id'])
    op.create_index('ix_promotion_orders_dates', 'promotion_orders', ['start_date', 'end_date'])
    op.create_index('ix_promotion_orders_active', 'promotion_orders', ['status', 'start_date', 'end_date'])
    
    # 5. 创建索引以优化查询性能
    op.create_index('ix_merchants_subscription', 'merchants', ['subscription_tier', 'subscription_expires_at'])


def downgrade():
    """回滚订阅功能"""
    
    # 删除新增的表
    op.drop_table('promotion_orders')
    op.drop_table('merchant_subscriptions')
    
    # 删除merchants表的新字段
    op.drop_index('ix_merchants_subscription', table_name='merchants')
    op.drop_column('merchants', 'subscription_auto_renew')
    op.drop_column('merchants', 'subscription_expires_at')
    op.drop_column('merchants', 'subscription_tier')