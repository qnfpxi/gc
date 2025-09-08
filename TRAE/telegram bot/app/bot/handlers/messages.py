"""
Bot 消息处理器

处理用户发送的各种消息
"""

from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext

from app.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(F.content_type == ContentType.TEXT)
async def handle_text_message(message: Message, state: FSMContext):
    """处理文本消息"""
    user_data = await state.get_data()
    
    # 检查用户是否已认证
    if not user_data.get("authenticated"):
        await message.answer(
            "👋 请先使用 /start 命令开始使用本服务！"
        )
        return
    
    text = message.text.lower() if message.text else ""
    
    # 简单的文本意图识别
    if any(word in text for word in ["广告", "发布", "创建", "卖", "出售"]):
        await message.answer(
            "📝 看起来您想要发布广告！\n\n"
            "请点击下方按钮开始创建：",
            reply_markup={"inline_keyboard": [[
                {"text": "📝 发布广告", "callback_data": "create_ad"}
            ]]}
        )
    
    elif any(word in text for word in ["搜索", "查找", "找", "浏览"]):
        await message.answer(
            "🔍 您可以浏览和搜索广告！\n\n"
            "请选择浏览方式：",
            reply_markup={"inline_keyboard": [
                [
                    {"text": "🔍 浏览广告", "callback_data": "browse_ads"},
                    {"text": "📍 附近广告", "callback_data": "nearby_ads"}
                ]
            ]}
        )
    
    elif any(word in text for word in ["帮助", "help", "怎么", "如何"]):
        await message.answer(
            "❓ 需要帮助吗？\n\n"
            "请使用 /help 命令查看详细使用指南，或选择下方选项：",
            reply_markup={"inline_keyboard": [
                [
                    {"text": "📖 使用指南", "callback_data": "show_guide"},
                    {"text": "🎧 联系客服", "callback_data": "contact_support"}
                ]
            ]}
        )
    
    else:
        # 默认响应
        await message.answer(
            "🤔 我不太理解您的意思。\n\n"
            "您可以：\n"
            "• 使用 /help 查看帮助\n"
            "• 点击菜单选择功能\n"
            "• 发送 /start 返回主菜单"
        )


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo_message(message: Message, state: FSMContext):
    """处理图片消息"""
    user_data = await state.get_data()
    
    if not user_data.get("authenticated"):
        await message.answer("👋 请先使用 /start 命令开始使用本服务！")
        return
    
    # 检查是否在广告创建流程中
    current_state = await state.get_state()
    
    if current_state and "create_ad" in current_state:
        # 在广告创建流程中，由相应的处理器处理
        return
    
    # 不在特定流程中，提供选择
    await message.answer(
        "📷 收到您的图片！\n\n"
        "您想要：",
        reply_markup={"inline_keyboard": [
            [
                {"text": "📝 用这张图片发布广告", "callback_data": "create_ad_with_photo"}
            ],
            [
                {"text": "🔍 搜索类似广告", "callback_data": "search_similar"}
            ]
        ]}
    )


@router.message(F.content_type == ContentType.LOCATION)
async def handle_location_message(message: Message, state: FSMContext):
    """处理位置消息"""
    user_data = await state.get_data()
    
    if not user_data.get("authenticated"):
        await message.answer("👋 请先使用 /start 命令开始使用本服务！")
        return
    
    location = message.location
    if not location:
        await message.answer("❌ 无法获取位置信息")
        return
    
    # 检查是否在广告创建流程中
    current_state = await state.get_state()
    
    if current_state and "create_ad" in current_state:
        # 在广告创建流程中，由相应的处理器处理
        return
    
    # 保存位置信息
    await state.update_data({
        "user_location": {
            "latitude": location.latitude,
            "longitude": location.longitude
        }
    })
    
    await message.answer(
        f"📍 位置已保存！\n\n"
        f"经度: {location.longitude:.6f}\n"
        f"纬度: {location.latitude:.6f}\n\n"
        f"您想要：",
        reply_markup={"inline_keyboard": [
            [
                {"text": "📍 查看附近广告", "callback_data": "nearby_ads"}
            ],
            [
                {"text": "📝 在此位置发布广告", "callback_data": "create_ad_here"}
            ]
        ]}
    )


@router.message(F.content_type == ContentType.CONTACT)
async def handle_contact_message(message: Message, state: FSMContext):
    """处理联系人消息"""
    user_data = await state.get_data()
    
    if not user_data.get("authenticated"):
        await message.answer("👋 请先使用 /start 命令开始使用本服务！")
        return
    
    contact = message.contact
    if not contact:
        await message.answer("❌ 无法获取联系人信息")
        return
    
    # 检查是否是用户自己的联系人
    if contact.user_id == message.from_user.id:
        await message.answer(
            "📞 联系方式已保存！\n\n"
            "这将作为您发布广告时的默认联系方式。",
            reply_markup={"inline_keyboard": [[
                {"text": "📝 现在发布广告", "callback_data": "create_ad"}
            ]]}
        )
    else:
        await message.answer(
            "❓ 您分享了其他人的联系方式。\n\n"
            "如果需要更新您的联系信息，请分享您自己的联系人卡片。"
        )


@router.message(F.content_type.in_({
    ContentType.DOCUMENT,
    ContentType.AUDIO,
    ContentType.VIDEO,
    ContentType.VOICE,
    ContentType.VIDEO_NOTE,
    ContentType.STICKER,
    ContentType.ANIMATION
}))
async def handle_media_message(message: Message, state: FSMContext):
    """处理媒体消息"""
    user_data = await state.get_data()
    
    if not user_data.get("authenticated"):
        await message.answer("👋 请先使用 /start 命令开始使用本服务！")
        return
    
    content_type = message.content_type
    
    if content_type == ContentType.DOCUMENT:
        await message.answer(
            "📄 收到您的文档！\n\n"
            "目前支持图片格式的广告。如果这是图片文件，"
            "建议直接发送图片以获得更好的体验。"
        )
    
    elif content_type in (ContentType.VIDEO, ContentType.ANIMATION):
        await message.answer(
            "🎥 收到您的视频！\n\n"
            "视频广告功能即将上线，敬请期待！\n"
            "目前建议使用图片发布广告。",
            reply_markup={"inline_keyboard": [[
                {"text": "📝 发布图片广告", "callback_data": "create_ad"}
            ]]}
        )
    
    elif content_type == ContentType.STICKER:
        await message.answer(
            "😄 可爱的贴纸！\n\n"
            "让我们开始创建您的广告吧：",
            reply_markup={"inline_keyboard": [[
                {"text": "📝 发布广告", "callback_data": "create_ad"}
            ]]}
        )
    
    else:
        await message.answer(
            "📎 收到您的媒体文件！\n\n"
            "目前主要支持图片和文字广告。\n"
            "让我们开始创建广告吧：",
            reply_markup={"inline_keyboard": [[
                {"text": "📝 发布广告", "callback_data": "create_ad"}
            ]]}
        )


@router.message()
async def handle_other_messages(message: Message, state: FSMContext):
    """处理其他类型的消息"""
    logger.info("Received unhandled message", 
               user_id=message.from_user.id if message.from_user else None,
               content_type=message.content_type)
    
    await message.answer(
        "🤔 这种消息类型我还不太会处理。\n\n"
        "请使用 /help 查看支持的功能，或选择菜单操作。",
        reply_markup={"inline_keyboard": [[
            {"text": "🏠 返回主菜单", "callback_data": "back_to_main"}
        ]]}
    )