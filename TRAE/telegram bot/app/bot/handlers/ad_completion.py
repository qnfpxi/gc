"""
广告创建流程完成部分

处理位置信息、联系方式和最终提交
"""

import json
import aiohttp
from typing import Optional
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardButton, 
    InlineKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext

from app.bot.states import AdCreationStates
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(AdCreationStates.waiting_for_location, F.location)
async def handle_location_input(message: Message, state: FSMContext):
    """处理位置信息"""
    location = message.location
    
    # 保存位置信息
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["latitude"] = location.latitude
    ad_data["longitude"] = location.longitude
    await state.update_data(ad_data=ad_data)
    
    await message.answer(
        f"✅ 位置已保存\n"
        f"📍 坐标: {location.latitude:.6f}, {location.longitude:.6f}\n\n"
        "📞 **请设置联系方式**\n\n"
        "买家如何联系您？",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 使用 Telegram", callback_data="contact_telegram")],
            [InlineKeyboardButton(text="📞 输入手机号", callback_data="contact_phone")],
            [InlineKeyboardButton(text="📧 输入邮箱", callback_data="contact_email")],
            [InlineKeyboardButton(text="⏭ 跳过联系方式", callback_data="skip_contact")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_contact)


@router.callback_query(AdCreationStates.waiting_for_location, F.data == "skip_location")
async def skip_location(callback: CallbackQuery, state: FSMContext):
    """跳过位置设置"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📞 **请设置联系方式**\n\n"
        "买家如何联系您？",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 使用 Telegram", callback_data="contact_telegram")],
            [InlineKeyboardButton(text="📞 输入手机号", callback_data="contact_phone")],
            [InlineKeyboardButton(text="📧 输入邮箱", callback_data="contact_email")],
            [InlineKeyboardButton(text="⏭ 跳过联系方式", callback_data="skip_contact")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_contact)


@router.callback_query(AdCreationStates.waiting_for_contact, F.data == "contact_telegram")
async def set_telegram_contact(callback: CallbackQuery, state: FSMContext):
    """设置 Telegram 联系方式"""
    await callback.answer()
    
    user = callback.from_user
    telegram_username = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    
    # 保存联系方式
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["contact_telegram"] = telegram_username
    await state.update_data(ad_data=ad_data)
    
    await proceed_to_confirmation(callback.message, state)


@router.callback_query(AdCreationStates.waiting_for_contact, F.data == "contact_phone")
async def request_phone_contact(callback: CallbackQuery, state: FSMContext):
    """请求输入手机号"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📞 **请输入您的手机号码**\n\n"
        "格式示例：\n"
        "• 13800138000\n"
        "• +86 138 0013 8000\n"
        "• 138-0013-8000",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回联系方式选择", callback_data="back_to_contact_selection")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    # 临时设置状态来等待手机号输入
    await state.update_data(waiting_for="phone")


@router.callback_query(AdCreationStates.waiting_for_contact, F.data == "contact_email")
async def request_email_contact(callback: CallbackQuery, state: FSMContext):
    """请求输入邮箱"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📧 **请输入您的邮箱地址**\n\n"
        "格式示例：\n"
        "• example@gmail.com\n"
        "• user@example.com",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回联系方式选择", callback_data="back_to_contact_selection")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    # 临时设置状态来等待邮箱输入
    await state.update_data(waiting_for="email")


@router.message(AdCreationStates.waiting_for_contact, F.text)
async def handle_contact_input(message: Message, state: FSMContext):
    """处理联系方式输入"""
    data = await state.get_data()
    waiting_for = data.get("waiting_for")
    
    if waiting_for == "phone":
        # 验证手机号格式
        phone = message.text.strip()
        # 简单的手机号验证
        import re
        phone_pattern = r'^(\+?86)?[\s\-]?1[3-9]\d{9}$'
        if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
            await message.answer(
                "❌ 手机号格式不正确，请重新输入。\n"
                "示例：13800138000"
            )
            return
        
        # 保存手机号
        ad_data = data.get("ad_data", {})
        ad_data["contact_phone"] = phone
        await state.update_data(ad_data=ad_data, waiting_for=None)
        
        await message.answer("✅ 手机号已保存")
        await proceed_to_confirmation(message, state)
        
    elif waiting_for == "email":
        # 验证邮箱格式
        email = message.text.strip()
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            await message.answer(
                "❌ 邮箱格式不正确，请重新输入。\n"
                "示例：example@gmail.com"
            )
            return
        
        # 保存邮箱
        ad_data = data.get("ad_data", {})
        ad_data["contact_email"] = email
        await state.update_data(ad_data=ad_data, waiting_for=None)
        
        await message.answer("✅ 邮箱已保存")
        await proceed_to_confirmation(message, state)


@router.callback_query(AdCreationStates.waiting_for_contact, F.data == "skip_contact")
async def skip_contact(callback: CallbackQuery, state: FSMContext):
    """跳过联系方式设置"""
    await callback.answer()
    
    # 使用 Telegram 作为默认联系方式
    user = callback.from_user
    telegram_username = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["contact_telegram"] = telegram_username
    await state.update_data(ad_data=ad_data)
    
    await proceed_to_confirmation(callback.message, state)


async def proceed_to_confirmation(message: Message, state: FSMContext):
    """进入确认发布步骤"""
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    
    # 生成预览文本
    preview_text = generate_ad_preview(ad_data)
    
    await message.answer(
        "📋 **广告预览**\n\n" + preview_text + "\n\n"
        "请确认信息是否正确：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ 确认发布", callback_data="confirm_publish")],
            [InlineKeyboardButton(text="✏️ 修改信息", callback_data="edit_ad_info")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ]),
        parse_mode="Markdown"
    )
    
    await state.set_state(AdCreationStates.waiting_for_confirmation)


@router.callback_query(AdCreationStates.waiting_for_confirmation, F.data == "confirm_publish")
async def confirm_publish_ad(callback: CallbackQuery, state: FSMContext):
    """确认发布广告"""
    await callback.answer()
    
    # 显示发布中消息
    publishing_msg = await callback.message.edit_text(
        "🚀 **正在发布广告...**\n\n"
        "请稍候，我们正在处理您的广告。"
    )
    
    try:
        data = await state.get_data()
        ad_data = data.get("ad_data", {})
        access_token = data.get("access_token")
        
        if not access_token:
            await publishing_msg.edit_text(
                "❌ 认证已过期，请重新开始。"
            )
            await state.clear()
            return
        
        # 调用 API 创建广告
        ad_result = await create_ad_via_api(ad_data, access_token)
        
        if ad_result:
            # 发布成功
            await publishing_msg.edit_text(
                "🎉 **广告发布成功！**\n\n"
                f"📝 标题：{ad_data.get('title', 'N/A')}\n"
                f"💰 价格：{format_price(ad_data)}\n"
                f"🆔 广告ID：{ad_result.get('id', 'N/A')}\n\n"
                "您的广告现在已经上线，买家可以看到并联系您！",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👀 查看我的广告", callback_data="my_ads")],
                    [InlineKeyboardButton(text="🏠 返回主菜单", callback_data="back_to_main")]
                ])
            )
            
            # 清理状态
            await state.clear()
            
            logger.info("Ad published successfully", 
                       ad_id=ad_result.get('id'),
                       user_id=data.get('user_id'))
        else:
            await publishing_msg.edit_text(
                "❌ **广告发布失败**\n\n"
                "服务器暂时无法处理您的请求，请稍后重试。",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 重试", callback_data="confirm_publish")],
                    [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
                ])
            )
    
    except Exception as e:
        logger.error("Error publishing ad", error=str(e))
        await publishing_msg.edit_text(
            "❌ **发布过程中出现错误**\n\n"
            "请稍后重试或联系客服。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 重试", callback_data="confirm_publish")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
            ])
        )


def generate_ad_preview(ad_data: dict) -> str:
    """生成广告预览文本"""
    preview = []
    
    # 标题
    if title := ad_data.get("title"):
        preview.append(f"📝 **标题**: {title}")
    
    # 价格
    price_text = format_price(ad_data)
    preview.append(f"💰 **价格**: {price_text}")
    
    # 描述
    if description := ad_data.get("description"):
        desc_preview = description[:100] + "..." if len(description) > 100 else description
        preview.append(f"📄 **描述**: {desc_preview}")
    
    # 图片
    images = ad_data.get("images", [])
    if images:
        preview.append(f"📸 **图片**: {len(images)} 张")
    
    # 位置
    if ad_data.get("latitude") and ad_data.get("longitude"):
        preview.append("📍 **位置**: 已设置")
    
    # 联系方式
    contact_methods = []
    if ad_data.get("contact_telegram"):
        contact_methods.append("Telegram")
    if ad_data.get("contact_phone"):
        contact_methods.append("电话")
    if ad_data.get("contact_email"):
        contact_methods.append("邮箱")
    
    if contact_methods:
        preview.append(f"📞 **联系方式**: {', '.join(contact_methods)}")
    
    return "\n".join(preview)


def format_price(ad_data: dict) -> str:
    """格式化价格显示"""
    if ad_data.get("is_negotiable") or ad_data.get("price") is None:
        return "面议"
    else:
        price = ad_data.get("price", 0)
        currency = ad_data.get("currency", "CNY")
        if currency == "CNY":
            return f"¥{price:,.2f}"
        else:
            return f"{price:,.2f} {currency}"


async def create_ad_via_api(ad_data: dict, access_token: str) -> Optional[dict]:
    """通过 API 创建广告"""
    try:
        # 准备 API 请求数据
        api_data = {
            "title": ad_data.get("title"),
            "description": ad_data.get("description"),
            "category_id": ad_data.get("category_id"),
            "price": ad_data.get("price"),
            "currency": ad_data.get("currency", "CNY"),
            "is_negotiable": ad_data.get("is_negotiable", False),
            "images": ad_data.get("images", []),
            "contact_telegram": ad_data.get("contact_telegram"),
            "contact_phone": ad_data.get("contact_phone"),
            "contact_email": ad_data.get("contact_email"),
        }
        
        # 添加位置信息（如果有）
        if ad_data.get("latitude") and ad_data.get("longitude"):
            api_data["latitude"] = ad_data["latitude"]
            api_data["longitude"] = ad_data["longitude"]
        
        # 调用 API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            async with session.post(
                f"{settings.API_BASE_URL}/api/v1/ads/",
                json=api_data,
                headers=headers
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error("API error creating ad", 
                               status=response.status, 
                               error=error_text)
                    return None
                    
    except Exception as e:
        logger.error("Error calling ad creation API", error=str(e))
        return None