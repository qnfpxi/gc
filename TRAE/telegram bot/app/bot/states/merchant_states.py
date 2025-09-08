"""
商家相关状态机

B2C平台的商家入驻和管理流程
"""

from aiogram.fsm.state import State, StatesGroup


class MerchantOnboardingStates(StatesGroup):
    """商家入驻状态组"""
    
    # 选择地区
    choosing_region = State()
    
    # 输入商家基本信息
    entering_name = State()
    entering_description = State()
    uploading_logo = State()
    
    # 位置和联系方式
    entering_address = State()
    sharing_location = State()
    entering_contact = State()
    
    # 营业时间
    setting_business_hours = State()
    
    # 确认入驻
    confirming_onboarding = State()


class ProductManagementStates(StatesGroup):
    """商品管理状态组"""
    
    # 选择操作
    choosing_action = State()
    
    # 发布新商品
    choosing_product_category = State()
    entering_product_name = State()
    entering_product_description = State()
    setting_product_price = State()
    uploading_product_images = State()
    adding_product_tags = State()
    confirming_product = State()
    
    # 管理现有商品
    selecting_product = State()
    editing_product_field = State()
    confirming_product_update = State()


class CustomerSearchStates(StatesGroup):
    """客户搜索状态组"""
    
    # 选择地区
    choosing_search_region = State()
    
    # 搜索和浏览
    browsing_categories = State()
    viewing_search_results = State()
    viewing_product_details = State()
    viewing_merchant_details = State()
    
    # 收藏和联系
    managing_favorites = State()
    contacting_merchant = State()