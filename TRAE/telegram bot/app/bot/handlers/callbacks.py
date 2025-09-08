"""
Bot 回调查询处理器

处理内联键盘按钮的回调
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from app.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


# create_ad 回调已移动到 ad_creation.py 中处理


@router.callback_query(F.data == "browse_ads")
async def browse_ads_callback(callback: CallbackQuery, state: FSMContext):
    """处理浏览广告回调"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔍 **浏览广告**\n\n"
        "广告浏览功能正在开发中...\n\n"
        "即将支持：\n"
        "• 📂 按分类浏览\n"
        "• 🔍 关键词搜索\n"
        "• 📍 地理位置筛选\n"
        "• 💰 价格区间筛选\n"
        "• ⭐ 推荐算法",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "nearby_ads")
async def nearby_ads_callback(callback: CallbackQuery, state: FSMContext):
    """处理附近广告回调"""
    await callback.answer()
    
    user_data = await state.get_data()
    user_location = user_data.get("user_location")
    
    if not user_location:
        await callback.message.edit_text(
            "📍 **查看附近广告**\n\n"
            "需要您的位置信息才能查找附近的广告。\n\n"
            "请点击下方按钮分享位置：",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📍 分享位置", request_location=True)],
                [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ])
        )
    else:
        await callback.message.edit_text(
            f"📍 **附近广告**\n\n"
            f"正在搜索您附近的广告...\n\n"
            f"当前位置：{user_location['latitude']:.4f}, {user_location['longitude']:.4f}\n\n"
            f"附近广告功能正在开发中，即将上线！",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 更新位置", request_location=True)],
                [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ])
        )


@router.callback_query(F.data == "my_ads")
async def my_ads_callback(callback: CallbackQuery, state: FSMContext):
    """处理我的广告回调"""
    await callback.answer()
    
    await callback.message.edit_text(
        "👤 **我的广告**\n\n"
        "我的广告管理功能正在开发中...\n\n"
        "即将支持：\n"
        "• 📋 查看已发布广告\n"
        "• ✏️ 编辑广告信息\n"
        "• 📊 查看浏览统计\n"
        "• 💬 管理询问消息\n"
        "• ⏰ 广告续期",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery, state: FSMContext):
    """返回主菜单"""
    await callback.answer()
    
    user = callback.from_user
    welcome_text = f"""
🎉 智能广告平台

👋 欢迎回来，{user.first_name}！

选择您想要的操作：
    """.strip()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 发布广告", callback_data="create_ad"),
            InlineKeyboardButton(text="🔍 浏览广告", callback_data="browse_ads"),
        ],
        [
            InlineKeyboardButton(text="📍 附近广告", callback_data="nearby_ads"),
            InlineKeyboardButton(text="👤 我的广告", callback_data="my_ads"),
        ],
        [
            InlineKeyboardButton(text="📱 打开 Mini App", web_app={"url": "https://your-webapp-url.com"}),
        ],
    ])
    
    await callback.message.edit_text(welcome_text, reply_markup=keyboard)


@router.callback_query(F.data == "create_ad_with_photo")
async def create_ad_with_photo_callback(callback: CallbackQuery, state: FSMContext):
    """使用刚发送的图片创建广告"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📷 **使用图片创建广告**\n\n"
        "图片广告创建功能正在开发中...\n\n"
        "即将支持自动：\n"
        "• 🤖 AI 图片分析\n"
        "• 🏷️ 智能分类建议\n"
        "• 📝 自动生成描述\n"
        "• 💰 价格建议",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 手动创建广告", callback_data="create_ad")],
            [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "search_similar")
async def search_similar_callback(callback: CallbackQuery, state: FSMContext):
    """搜索类似广告"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔍 **以图搜广告**\n\n"
        "图片相似搜索功能正在开发中...\n\n"
        "即将支持：\n"
        "• 🔍 相似图片检索\n"
        "• 🏷️ 相似商品推荐\n"
        "• 💰 价格对比\n"
        "• 📊 市场分析",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 文字搜索", callback_data="browse_ads")],
            [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "create_ad_here")
async def create_ad_here_callback(callback: CallbackQuery, state: FSMContext):
    """在当前位置创建广告"""
    await callback.answer()
    
    user_data = await state.get_data()
    location = user_data.get("user_location")
    
    if location:
        await callback.message.edit_text(
            f"📍 **在此位置发布广告**\n\n"
            f"位置已设定：\n"
            f"• 纬度: {location['latitude']:.6f}\n"
            f"• 经度: {location['longitude']:.6f}\n\n"
            f"位置广告创建功能正在开发中...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 创建广告", callback_data="create_ad")],
                [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ])
        )
    else:
        await callback.message.edit_text(
            "❌ 未找到位置信息，请重新分享位置。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📍 分享位置", request_location=True)],
                [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ])
        )


# 设置相关的回调处理器
@router.callback_query(F.data.startswith("settings_"))
async def settings_callback(callback: CallbackQuery, state: FSMContext):
    """处理设置相关回调"""
    await callback.answer()
    
    setting_type = callback.data.split("_")[1]
    
    settings_text = {
        "notifications": "🔔 **通知设置**\n\n通知功能正在开发中...",
        "language": "🌍 **语言设置**\n\n多语言支持正在开发中...", 
        "location": "📍 **位置设置**\n\n位置偏好设置正在开发中...",
        "ui": "🎨 **界面设置**\n\n界面个性化正在开发中..."
    }
    
    text = settings_text.get(setting_type, "⚙️ 设置功能正在开发中...")
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ 返回设置", callback_data="back_to_settings")],
            [InlineKeyboardButton(text="🏠 返回主菜单", callback_data="back_to_main")]
        ])
    )


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings_callback(callback: CallbackQuery, state: FSMContext):
    """返回设置菜单"""
    await callback.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 通知设置", callback_data="settings_notifications"),
            InlineKeyboardButton(text="🌍 语言设置", callback_data="settings_language"),
        ],
        [
            InlineKeyboardButton(text="📍 位置设置", callback_data="settings_location"),
            InlineKeyboardButton(text="🎨 界面设置", callback_data="settings_ui"),
        ],
        [
            InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main"),
        ],
    ])
    
    await callback.message.edit_text(
        "⚙️ **设置中心**\n\n请选择要修改的设置项目：",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.in_({"show_guide", "contact_support"}))
async def help_callback(callback: CallbackQuery, state: FSMContext):
    """处理帮助相关回调"""
    await callback.answer()
    
    if callback.data == "show_guide":
        text = "📖 **使用指南**\n\n详细使用指南正在制作中..."
    else:
        text = "🎧 **联系客服**\n\n客服系统正在开发中..."
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
        ])
    )