"""
B2C平台主菜单处理器

处理消费者和商家的不同入口
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from app.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


async def show_main_menu(callback_or_message, user_data: dict):
    """显示主菜单 - 根据用户类型和聊天类型显示不同选项"""
    user_id = user_data.get("user_id")
    is_merchant = user_data.get("is_merchant", False)
    
    # 获取聊天类型
    if hasattr(callback_or_message, 'chat'):
        chat_type = callback_or_message.chat.type
    elif hasattr(callback_or_message, 'message') and hasattr(callback_or_message.message, 'chat'):
        chat_type = callback_or_message.message.chat.type
    else:
        chat_type = "private"  # 默认为私聊
    
    # 根据聊天类型显示不同菜单
    if chat_type in ["group", "supergroup"]:
        # 群聊模式：主要是搜索功能
        text = "🔍 **商家搜索平台**\\n\\n" \
               "🚀 在群聊中快速搜索商家和服务："
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 搜索商家", callback_data="group_search_merchants"),
                InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby_merchants"),
            ],
            [
                InlineKeyboardButton(text="🏢 选择地区", callback_data="group_choose_region"),
                InlineKeyboardButton(text="🏪 热门商家", callback_data="group_popular_merchants"),
            ],
            [
                InlineKeyboardButton(text="💬 私聊机器人", url="https://t.me/YourBotUsername"),
            ],
        ])
    elif is_merchant:
        # 私聊模式 - 商家菜单
        text = "🏪 **商家管理中心**\\n\\n" \
               "欢迎回来！选择您要进行的操作："
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 管理后台(React)", web_app={"url": "https://cold-snails-return.loca.lt"}),
            ],
            [
                InlineKeyboardButton(text="🧪 基础测试页面", web_app={"url": "https://cold-snails-return.loca.lt/test.html"}),
            ],
            [
                InlineKeyboardButton(text="📦 发布商品", callback_data="add_product"),
                InlineKeyboardButton(text="🛍️ 管理商品", callback_data="manage_products"),
            ],
            [
                InlineKeyboardButton(text="🏪 店铺设置", callback_data="merchant_settings"),
                InlineKeyboardButton(text="📊 经营数据", callback_data="merchant_analytics"),
            ],
            [
                InlineKeyboardButton(text="💬 客户消息", callback_data="customer_messages"),
                InlineKeyboardButton(text="⭐ 评价管理", callback_data="review_management"),
            ],
            [
                InlineKeyboardButton(text="👤 切换到消费者模式", callback_data="switch_to_customer"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ 帮助", callback_data="help"),
                InlineKeyboardButton(text="⚙️ 设置", callback_data="settings"),
            ],
        ])
    else:
        # 消费者菜单  
        text = "🛍️ **本地服务平台**\\n\\n" \
               "发现您身边的优质商家和服务："
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📍 选择地区", callback_data="choose_region"),
            ],
            [
                InlineKeyboardButton(text="🔍 搜索商家", callback_data="search_merchants"),
                InlineKeyboardButton(text="🛒 浏览商品", callback_data="browse_products"),
            ],
            [
                InlineKeyboardButton(text="⭐ 我的收藏", callback_data="my_favorites"),
                InlineKeyboardButton(text="📜 浏览记录", callback_data="view_history"),
            ],
            [
                InlineKeyboardButton(text="🏪 成为商家", callback_data="become_merchant"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ 帮助", callback_data="help"),
                InlineKeyboardButton(text="⚙️ 设置", callback_data="settings"),
            ],
        ])
    
    if hasattr(callback_or_message, 'edit_text'):
        # 是CallbackQuery
        await callback_or_message.edit_text(
            text, 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )
    else:
        # 是Message
        await callback_or_message.answer(
            text, 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    """返回主菜单"""
    await callback.answer()
    
    user_data = await state.get_data()
    await show_main_menu(callback.message, user_data)


@router.callback_query(F.data == "become_merchant")
async def become_merchant_callback(callback: CallbackQuery, state: FSMContext):
    """成为商家或进入商家管理（仅限私聊）"""
    await callback.answer()
    
    # 检查是否为私聊
    chat_type = callback.message.chat.type
    if chat_type in ["group", "supergroup"]:
        await callback.message.edit_text(
            "❌ **商家入驻仅限私聊**\n\n"
            "🔒 为了保护您的隐私和安全，商家入驻功能仅在私聊中可用。\n\n"
            "💬 请点击下方按钮私聊机器人开始入驻：",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 私聊机器人入驻", url="https://t.me/YourBotUsername")],
                [InlineKeyboardButton(text="🔙 返回", callback_data="back_to_group_main")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # TODO: 检查用户是否已经是商家
    # 这里先模拟检查逻辑
    user_id = callback.from_user.id
    
    # 模拟检查数据库（实际应该调用API）
    is_existing_merchant = False  # 这里应该查询数据库
    
    if is_existing_merchant:
        # 已经是商家，进入商家管理菜单
        user_data = await state.get_data()
        user_data["is_merchant"] = True
        await state.update_data(user_data)
        await show_main_menu(callback.message, user_data)
    else:
        # 还不是商家，显示入驻页面
        await callback.message.edit_text(
            "🏪 **商家入驻**\\n\\n"
            "欢迎加入我们的平台！\\n"
            "成为认证商家，您可以：\\n\\n"
            "• 📦 发布和管理商品/服务\\n"
            "• 🏪 建立专属店铺页面\\n"
            "• 📊 查看经营数据分析\\n"
            "• 💬 直接与客户沟通\\n"
            "• ⭐ 获得客户评价和口碑\\n\\n"
            "让我们开始商家入驻流程吧！",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 开始入驻", callback_data="start_merchant_onboarding")],
                [InlineKeyboardButton(text="📋 入驻须知", callback_data="merchant_terms")],
                [InlineKeyboardButton(text="🔙 返回", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "switch_to_customer")
async def switch_to_customer_callback(callback: CallbackQuery, state: FSMContext):
    """切换到消费者模式"""
    await callback.answer()
    
    # 更新用户数据
    user_data = await state.get_data()
    user_data["is_merchant"] = False
    await state.update_data(user_data)
    
    await show_main_menu(callback.message, user_data)


@router.callback_query(F.data == "choose_region")
async def choose_region_callback(callback: CallbackQuery, state: FSMContext):
    """选择地区"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📍 **选择您的地区**\\n\\n"
        "请选择您所在的城市，我们将为您推荐附近的商家和服务：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏙️ 北京市", callback_data="region_1"),
                InlineKeyboardButton(text="🌃 上海市", callback_data="region_7"),
            ],
            [
                InlineKeyboardButton(text="🌆 广州市", callback_data="region_12"),
                InlineKeyboardButton(text="🏘️ 其他城市", callback_data="other_regions"),
            ],
            [
                InlineKeyboardButton(text="📍 自动定位", callback_data="auto_location"),
            ],
            [
                InlineKeyboardButton(text="🔙 返回", callback_data="back_to_main")
            ]
        ]),
        parse_mode="Markdown"
    )