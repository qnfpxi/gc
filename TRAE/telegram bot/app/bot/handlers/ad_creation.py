"""
广告创建处理器

处理广告发布的完整对话流程
"""

import json
from typing import Dict, Any, List, Optional
from io import BytesIO

import aiohttp
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardButton, 
    InlineKeyboardMarkup, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext

from app.bot.states import AdCreationStates
from app.config import settings
from app.core.logging import get_logger
# 从认证中间件导入（暂时注释，因为函数不存在）
# from app.bot.middlewares.auth import get_user_token

logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data == "create_ad")
async def start_ad_creation(callback: CallbackQuery, state: FSMContext):
    """开始广告创建流程"""
    await callback.answer()
    
    user_data = await state.get_data()
    if not user_data.get("authenticated"):
        await callback.message.edit_text(
            "❌ 请先使用 /start 命令进行认证"
        )
        return
    
    # 清理之前的状态数据
    await state.clear()
    await state.update_data({
        "authenticated": user_data.get("authenticated"),
        "access_token": user_data.get("access_token"),
        "user_id": user_data.get("user_id"),
        "ad_data": {}  # 存储广告数据
    })
    
    # 获取分类列表
    try:
        access_token = user_data.get("access_token")
        categories = await fetch_categories(access_token)
        
        if not categories:
            await callback.message.edit_text(
                "❌ 暂时无法获取分类信息，请稍后重试。",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
                ])
            )
            return
        
        # 创建分类选择键盘
        keyboard = create_category_keyboard(categories)
        
        await callback.message.edit_text(
            "📝 **发布新广告**\n\n"
            "请选择广告分类：",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # 设置状态
        await state.set_state(AdCreationStates.waiting_for_category)
        
    except Exception as e:
        logger.error("Error starting ad creation", error=str(e))
        await callback.message.edit_text(
            "❌ 启动广告创建失败，请稍后重试。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 返回主菜单", callback_data="back_to_main")]
            ])
        )


@router.callback_query(AdCreationStates.waiting_for_category, F.data.startswith("category_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    """处理分类选择"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[1])
    
    # 保存分类ID
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["category_id"] = category_id
    await state.update_data(ad_data=ad_data)
    
    await callback.message.edit_text(
        "✅ 分类已选择\n\n"
        "📝 **请输入广告标题**\n\n"
        "标题应该简洁明了，突出商品/服务的主要特点。\n"
        "例如：「iPhone 14 Pro 256GB 深空黑 9成新」",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 重新选择分类", callback_data="create_ad")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_title)


@router.message(AdCreationStates.waiting_for_title, F.text)
async def handle_title_input(message: Message, state: FSMContext):
    """处理标题输入"""
    title = message.text.strip()
    
    if len(title) < 5:
        await message.answer(
            "❌ 标题太短，请输入至少5个字符的标题。"
        )
        return
    
    if len(title) > 200:
        await message.answer(
            "❌ 标题太长，请输入不超过200个字符的标题。"
        )
        return
    
    # 保存标题
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["title"] = title
    await state.update_data(ad_data=ad_data)
    
    await message.answer(
        f"✅ 标题已保存：{title}\n\n"
        "📄 **请输入详细描述**\n\n"
        "请详细描述您的商品/服务，包括：\n"
        "• 商品状态和成色\n"
        "• 购买时间和使用情况\n"
        "• 包装配件是否齐全\n"
        "• 其他重要信息\n\n"
        "描述越详细，越容易吸引买家！",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 修改标题", callback_data="edit_title")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_description)


@router.message(AdCreationStates.waiting_for_description, F.text)
async def handle_description_input(message: Message, state: FSMContext):
    """处理描述输入"""
    description = message.text.strip()
    
    if len(description) < 10:
        await message.answer(
            "❌ 描述太短，请输入至少10个字符的详细描述。"
        )
        return
    
    if len(description) > 2000:
        await message.answer(
            "❌ 描述太长，请控制在2000字符以内。"
        )
        return
    
    # 保存描述
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["description"] = description
    await state.update_data(ad_data=ad_data)
    
    await message.answer(
        "✅ 描述已保存\n\n"
        "💰 **请输入价格**\n\n"
        "请输入您期望的价格，格式：\n"
        "• 数字（例如：1500）\n"
        "• 或发送「面议」表示价格面议\n\n"
        "💡 小贴士：合理的定价更容易成交！",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 面议", callback_data="price_negotiable")],
            [InlineKeyboardButton(text="🔙 修改描述", callback_data="edit_description")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_price)


@router.message(AdCreationStates.waiting_for_price, F.text)
async def handle_price_input(message: Message, state: FSMContext):
    """处理价格输入"""
    price_text = message.text.strip()
    
    # 保存价格
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    
    if price_text.lower() in ["面议", "面谈", "negotiable"]:
        ad_data["price"] = None
        ad_data["is_negotiable"] = True
        price_display = "面议"
    else:
        try:
            price = float(price_text)
            if price < 0:
                await message.answer("❌ 价格不能为负数，请重新输入。")
                return
            if price > 10000000:  # 1000万上限
                await message.answer("❌ 价格过高，请输入合理的价格。")
                return
            
            ad_data["price"] = price
            ad_data["is_negotiable"] = False
            ad_data["currency"] = "CNY"
            price_display = f"¥{price:,.2f}"
        except ValueError:
            await message.answer(
                "❌ 价格格式不正确。\n"
                "请输入数字（如：1500）或发送「面议」。"
            )
            return
    
    await state.update_data(ad_data=ad_data)
    
    await message.answer(
        f"✅ 价格已设置：{price_display}\n\n"
        "📸 **请上传广告图片**\n\n"
        "• 最多可上传5张图片\n"
        "• 支持 JPG、PNG、WebP 格式\n"
        "• 每张图片不超过10MB\n\n"
        "请发送第一张图片，或点击「跳过」继续：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ 跳过图片", callback_data="skip_images")],
            [InlineKeyboardButton(text="🔙 修改价格", callback_data="edit_price")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_images)


@router.callback_query(AdCreationStates.waiting_for_price, F.data == "price_negotiable")
async def handle_price_negotiable(callback: CallbackQuery, state: FSMContext):
    """处理面议价格"""
    await callback.answer()
    
    # 保存面议价格
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    ad_data["price"] = None
    ad_data["is_negotiable"] = True
    await state.update_data(ad_data=ad_data)
    
    await callback.message.edit_text(
        "✅ 价格已设置：面议\n\n"
        "📸 **请上传广告图片**\n\n"
        "• 最多可上传5张图片\n"
        "• 支持 JPG、PNG、WebP 格式\n"
        "• 每张图片不超过10MB\n\n"
        "请发送第一张图片，或点击「跳过」继续：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ 跳过图片", callback_data="skip_images")],
            [InlineKeyboardButton(text="🔙 修改价格", callback_data="edit_price")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_images)


@router.message(AdCreationStates.waiting_for_images, F.photo)
async def handle_image_upload(message: Message, state: FSMContext):
    """处理图片上传"""
    try:
        # 获取用户令牌
        data = await state.get_data()
        access_token = data.get("access_token")
        
        if not access_token:
            await message.answer("❌ 认证已过期，请重新开始。")
            await state.clear()
            return
        
        # 获取最大尺寸的图片
        photo = message.photo[-1]
        
        # 下载图片
        bot = message.bot
        file = await bot.get_file(photo.file_id)
        
        # 发送处理中消息
        processing_msg = await message.answer("📤 正在上传图片，请稍候...")
        
        # 上传到我们的 API
        image_url = await upload_image_to_api(bot, file, access_token)
        
        if image_url:
            # 保存图片URL
            ad_data = data.get("ad_data", {})
            images = ad_data.get("images", [])
            images.append(image_url)
            ad_data["images"] = images
            await state.update_data(ad_data=ad_data)
            
            await processing_msg.delete()
            
            images_count = len(images)
            keyboard = []
            
            if images_count < 5:
                keyboard.append([InlineKeyboardButton(text="📸 添加更多图片", callback_data="add_more_images")])
            
            keyboard.extend([
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="images_done")],
                [InlineKeyboardButton(text="🗑 删除最后一张", callback_data="delete_last_image")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
            ])
            
            await message.answer(
                f"✅ 图片上传成功！({images_count}/5)\n\n"
                f"当前已上传 {images_count} 张图片。\n"
                "您可以继续添加图片或进入下一步。",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await processing_msg.edit_text("❌ 图片上传失败，请重试。")
            
    except Exception as e:
        logger.error("Error uploading image", error=str(e))
        await message.answer("❌ 图片处理失败，请重试或跳过此步骤。")


@router.callback_query(AdCreationStates.waiting_for_images, F.data == "skip_images")
async def skip_images(callback: CallbackQuery, state: FSMContext):
    """跳过图片上传"""
    await callback.answer()
    await proceed_to_location(callback.message, state)


@router.callback_query(AdCreationStates.waiting_for_images, F.data == "add_more_images")
async def add_more_images(callback: CallbackQuery, state: FSMContext):
    """添加更多图片"""
    await callback.answer()
    await callback.message.edit_text(
        "📸 请继续发送图片，最多还可以上传 {} 张图片。".format(
            5 - len((await state.get_data()).get("ad_data", {}).get("images", []))
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ 图片完成", callback_data="images_done")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )


@router.callback_query(AdCreationStates.waiting_for_images, F.data == "delete_last_image")
async def delete_last_image(callback: CallbackQuery, state: FSMContext):
    """删除最后一张图片"""
    await callback.answer()
    
    # 获取当前图片列表
    data = await state.get_data()
    ad_data = data.get("ad_data", {})
    images = ad_data.get("images", [])
    
    if images:
        # 删除最后一张图片
        deleted_image = images.pop()
        ad_data["images"] = images
        await state.update_data(ad_data=ad_data)
        
        await callback.message.edit_text(
            f"🗑 已删除最后一张图片。\n\n当前已上传 {len(images)} 张图片。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📸 添加更多图片", callback_data="add_more_images")] if len(images) < 5 else [],
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="images_done")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
            ])
        )
    else:
        await callback.message.edit_text(
            "❌ 没有可删除的图片。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="images_done")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
            ])
        )


@router.callback_query(AdCreationStates.waiting_for_images, F.data == "images_done")
async def images_done(callback: CallbackQuery, state: FSMContext):
    """完成图片上传"""
    await callback.answer()
    await proceed_to_location(callback.message, state)


async def proceed_to_location(message: Message, state: FSMContext):
    """进入位置设置步骤"""
    await message.edit_text(
        "📍 **请分享您的位置**\n\n"
        "准确的位置信息有助于买家找到您。\n\n"
        "请点击下方按钮分享位置，或点击「跳过」：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📍 分享位置", request_location=True)],
            [InlineKeyboardButton(text="⏭ 跳过位置", callback_data="skip_location")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")]
        ])
    )
    
    await state.set_state(AdCreationStates.waiting_for_location)


# 辅助函数
async def fetch_categories(access_token: str) -> List[Dict]:
    """获取分类列表"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                f"{settings.API_BASE_URL}/api/v1/categories/",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("categories", [])
                return []
    except Exception as e:
        logger.error("Error fetching categories", error=str(e))
        return []


def create_category_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """创建分类选择键盘"""
    keyboard = []
    
    # 只显示根分类（没有父分类的）
    root_categories = [cat for cat in categories if not cat.get("parent_id")]
    
    # 按两列排列
    for i in range(0, len(root_categories), 2):
        row = []
        for j in range(2):
            if i + j < len(root_categories):
                cat = root_categories[i + j]
                icon = cat.get("icon", "📁")
                text = f"{icon} {cat['name']}"
                row.append(InlineKeyboardButton(
                    text=text,
                    callback_data=f"category_{cat['id']}"
                ))
        keyboard.append(row)
    
    # 添加取消按钮
    keyboard.append([
        InlineKeyboardButton(text="❌ 取消", callback_data="cancel_ad_creation")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def upload_image_to_api(bot, file, access_token: str) -> Optional[str]:
    """
    将图片上传到 API
    
    Args:
        bot: Bot 实例
        file: Telegram 文件对象
        access_token: 用户访问令牌
        
    Returns:
        Optional[str]: 图片 URL，失败时返回 None
    """
    try:
        # 下载文件内容
        file_content = BytesIO()
        await bot.download_file(file.file_path, file_content)
        file_content.seek(0)
        
        # 获取文件扩展名
        file_extension = ".jpg"  # 默认扩展名
        if file.file_path:
            import os
            file_extension = os.path.splitext(file.file_path)[1] or ".jpg"
        
        # 生成文件名
        filename = f"telegram_image_{file.file_unique_id}{file_extension}"
        
        # 准备上传数据
        form_data = aiohttp.FormData()
        form_data.add_field(
            'file',
            file_content,
            filename=filename,
            content_type='image/jpeg'
        )
        form_data.add_field('folder', 'ads')
        
        # 上传到 API
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with session.post(
                f"{settings.API_BASE_URL}/api/v1/media/upload/single",
                data=form_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("url")
                else:
                    error_text = await response.text()
                    logger.error("Image upload failed", 
                               status=response.status, 
                               error=error_text)
                    return None
                    
    except Exception as e:
        logger.error("Error uploading image to API", error=str(e))
        return None


@router.callback_query(F.data == "cancel_ad_creation")
async def cancel_ad_creation(callback: CallbackQuery, state: FSMContext):
    """取消广告创建"""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "❌ 广告创建已取消。\n\n"
        "您可以随时重新开始创建广告。",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 返回主菜单", callback_data="back_to_main")]
        ])
    )
