"""
广告发布状态机

定义广告创建过程中的各个状态
"""

from aiogram.fsm.state import State, StatesGroup


class AdCreationStates(StatesGroup):
    """广告创建状态组"""
    
    # 等待选择分类
    waiting_for_category = State()
    
    # 等待输入标题
    waiting_for_title = State()
    
    # 等待输入描述
    waiting_for_description = State()
    
    # 等待输入价格
    waiting_for_price = State()
    
    # 等待上传图片
    waiting_for_images = State()
    
    # 等待位置信息
    waiting_for_location = State()
    
    # 等待联系方式
    waiting_for_contact = State()
    
    # 确认发布
    waiting_for_confirmation = State()


class AdEditStates(StatesGroup):
    """广告编辑状态组"""
    
    # 选择要编辑的广告
    selecting_ad = State()
    
    # 选择编辑字段
    selecting_field = State()
    
    # 等待新值
    waiting_for_new_value = State()
    
    # 确认更新
    waiting_for_update_confirmation = State()


class AdSearchStates(StatesGroup):
    """广告搜索状态组"""
    
    # 等待搜索关键词
    waiting_for_keywords = State()
    
    # 等待选择分类过滤
    waiting_for_category_filter = State()
    
    # 等待价格范围
    waiting_for_price_range = State()
    
    # 等待位置过滤
    waiting_for_location_filter = State()
    
    # 显示搜索结果
    showing_results = State()


class MerchantOnboardingStates(StatesGroup):
    """商家入驻状态组"""
    
    # 等待输入店铺名称
    waiting_for_name = State()
    
    # 等待输入店铺描述
    waiting_for_description = State()
    
    # 等待选择地区
    waiting_for_region = State()
    
    # 等待输入详细地址
    waiting_for_address = State()
    
    # 等待输入联系方式
    waiting_for_contact = State()
    
    # 等待确认信息
    waiting_for_confirmation = State()