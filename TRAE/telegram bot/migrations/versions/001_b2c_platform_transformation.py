"""B2C Platform Transformation

Revision ID: 001_b2c_platform
Revises: 
Create Date: 2025-08-31 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '001_b2c_platform'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """升级到B2C商家平台架构"""
    
    # 1. 创建地区表 (顶级分类)
    op.create_table('regions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, comment='1:省, 2:市, 3:区/县'),
        sa.Column('code', sa.String(20), nullable=True, comment='行政区划代码'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['regions.id'], ),
        sa.CheckConstraint('level >= 1 AND level <= 3', name='check_level_range')
    )
    
    # 为地区表创建索引
    op.create_index('idx_regions_parent_level', 'regions', ['parent_id', 'level'])
    op.create_index('idx_regions_name', 'regions', ['name'])
    op.create_index('idx_regions_code', 'regions', ['code'])
    
    # 2. 创建商家表 (核心实体)
    op.create_table('merchants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联到Telegram用户'),
        sa.Column('name', sa.String(255), nullable=False, comment='商家名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='商家描述'),
        sa.Column('logo_url', sa.String(500), nullable=True, comment='商家Logo'),
        sa.Column('address', sa.String(500), nullable=True, comment='详细地址'),
        sa.Column('location', sa.String(100), nullable=True, comment='经纬度字符串'),
        sa.Column('region_id', sa.Integer(), nullable=False, comment='所属地区'),
        sa.Column('business_hours', sa.Text(), nullable=True, comment='营业时间JSON'),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_wechat', sa.String(100), nullable=True),
        sa.Column('contact_telegram', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending', comment='pending,active,suspended'),
        sa.Column('rating_avg', sa.Numeric(3, 2), nullable=True, default=0.0),
        sa.Column('rating_count', sa.Integer(), nullable=False, default=0),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ),
        sa.UniqueConstraint('user_id', name='unique_merchant_per_user')
    )
    
    # 为商家表创建索引
    op.create_index('idx_merchants_region_status', 'merchants', ['region_id', 'status'])
    op.create_index('idx_merchants_name', 'merchants', ['name'])
    op.create_index('idx_merchants_rating', 'merchants', ['rating_avg', 'rating_count'])
    
    # 3. 创建商品/服务分类表
    op.create_table('product_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(20), nullable=True, comment='分类图标emoji'),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['product_categories.id'], )
    )
    
    # 4. 创建商品/服务表 (替代原有广告表)
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False, comment='商品/服务名称'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_unit', sa.String(20), nullable=True, comment='次,小时,天,月等'),
        sa.Column('is_price_negotiable', sa.Boolean(), nullable=False, default=False),
        sa.Column('currency', sa.String(3), nullable=False, default='CNY'),
        sa.Column('image_urls', sa.Text(), nullable=True, comment='图片URL列表JSON'),
        sa.Column('tags', sa.Text(), nullable=True, comment='搜索标签JSON'),
        sa.Column('status', sa.String(20), nullable=False, default='active', comment='active,inactive,sold'),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('favorite_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['product_categories.id'], )
    )
    
    # 为商品表创建索引
    op.create_index('idx_products_merchant_status', 'products', ['merchant_id', 'status'])
    op.create_index('idx_products_category_status', 'products', ['category_id', 'status'])
    op.create_index('idx_products_name', 'products', ['name'])
    
    # 5. 创建用户收藏表
    op.create_table('user_favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('merchant_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'product_id', name='unique_user_product_favorite'),
        sa.UniqueConstraint('user_id', 'merchant_id', name='unique_user_merchant_favorite'),
        sa.CheckConstraint('(product_id IS NOT NULL) OR (merchant_id IS NOT NULL)', name='check_favorite_target')
    )
    
    # 6. 插入初始地区数据 (示例: 北京市)
    op.execute("""
        INSERT INTO regions (name, parent_id, level, code) VALUES 
        ('北京市', NULL, 1, '110000'),
        ('朝阳区', 1, 3, '110105'),
        ('海淀区', 1, 3, '110108'),
        ('丰台区', 1, 3, '110106'),
        ('西城区', 1, 3, '110102'),
        ('东城区', 1, 3, '110101'),
        
        ('上海市', NULL, 1, '310000'),
        ('浦东新区', 7, 3, '310115'),
        ('黄浦区', 7, 3, '310101'),
        ('徐汇区', 7, 3, '310104'),
        ('长宁区', 7, 3, '310105'),
        
        ('广州市', NULL, 1, '440100'),
        ('天河区', 12, 3, '440106'),
        ('越秀区', 12, 3, '440104'),
        ('海珠区', 12, 3, '440105')
    """)
    
    # 7. 插入初始商品分类数据
    op.execute("""
        INSERT INTO product_categories (name, parent_id, icon, sort_order) VALUES 
        ('餐饮美食', NULL, '🍽️', 1),
        ('生活服务', NULL, '🛠️', 2),
        ('休闲娱乐', NULL, '🎮', 3),
        ('购物零售', NULL, '🛍️', 4),
        ('教育培训', NULL, '📚', 5),
        ('医疗健康', NULL, '🏥', 6),
        
        ('中餐', 1, '🥢', 11),
        ('西餐', 1, '🍝', 12),
        ('快餐', 1, '🍔', 13),
        ('饮品', 1, '🧋', 14),
        
        ('家政服务', 2, '🏠', 21),
        ('维修服务', 2, '🔧', 22),
        ('美容美发', 2, '💇', 23),
        ('洗车洗衣', 2, '🚗', 24)
    """)


def downgrade():
    """回滚到原始架构"""
    op.drop_table('user_favorites')
    op.drop_table('products')
    op.drop_table('product_categories')
    op.drop_table('merchants')
    op.drop_table('regions')