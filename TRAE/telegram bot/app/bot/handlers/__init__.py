"""
Bot 处理器包

管理 Bot 的各种命令和消息处理器
"""

from aiogram import Router

from app.bot.handlers.commands import router as commands_router
from app.bot.handlers.messages import router as messages_router
from app.bot.handlers.callbacks import router as callbacks_router
from app.bot.handlers.main_menu import router as main_menu_router
from app.bot.handlers.merchant_onboarding import router as merchant_onboarding_router
from app.bot.handlers.group_search import router as group_search_router
from app.bot.handlers.product_management import router as product_management_router
# 旧的广告创建模块 - 将逐步替换
# from app.bot.handlers.ad_creation import router as ad_creation_router
# from app.bot.handlers.ad_completion import router as ad_completion_router


def get_main_router() -> Router:
    """获取主路由器"""
    main_router = Router()
    
    # 注册子路由器
    main_router.include_router(commands_router)
    main_router.include_router(main_menu_router)
    main_router.include_router(merchant_onboarding_router)  # 商家入驻流程
    main_router.include_router(group_search_router)  # 群聊搜索功能
    main_router.include_router(product_management_router)  # 商品管理功能
    main_router.include_router(callbacks_router)
    # main_router.include_router(ad_creation_router)  # 暂时禁用
    # main_router.include_router(ad_completion_router)  # 暂时禁用
    main_router.include_router(messages_router)
    
    return main_router