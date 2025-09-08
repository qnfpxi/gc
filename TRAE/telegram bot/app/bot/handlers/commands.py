"""
Bot 命令处理器

处理 Bot 的各种命令
"""

import json
from typing import Any, Dict

import aiohttp
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from app.config import settings
from app.core.logging import get_logger
from app.bot.middlewares.auth import AuthMiddleware

logger = get_logger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """处理 /start 命令"""
    user = message.from_user
    if not user:
        await message.answer("❌ 无法获取用户信息")
        return
    
    logger.info("Processing /start command", user_id=user.id, username=user.username)
    
    try:
        # 准备 Telegram 认证数据
        auth_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "is_premium": user.is_premium or False,
            "allows_write_to_pm": True,  # 如果能收到消息说明允许私聊
        }
        
        # 调用认证 API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.API_BASE_URL}/api/v1/auth/telegram",
                json={"telegram_user": auth_data},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    access_token = result.get("access_token")
                    
                    if access_token:
                        # 保存用户令牌到 Redis
                        await AuthMiddleware.save_user_token(
                            telegram_user_id=user.id,
                            access_token=access_token,
                            expires_in=1800  # 30 分钟
                        )
                        
                        # 检查用户是否为商家 (简化版本，实际需要查询数据库)
                        user_data_dict = {
                            "authenticated": True,
                            "access_token": access_token,
                            "user_id": result.get("user", {}).get("id"),
                            "is_merchant": False  # TODO: 从数据库查询实际状态
                        }
                        
                        # 显示新的主菜单
                        from app.bot.handlers.main_menu import show_main_menu
                        try:
                            await show_main_menu(message, user_data_dict)
                            logger.info("Main menu displayed successfully", user_id=user.id)
                        except Exception as menu_error:
                            logger.error("Failed to show main menu", user_id=user.id, error=str(menu_error))
                            # 降级方案：发送简单欢迎消息
                            await message.answer(
                                "🎉 欢迎使用智能广告平台！\n\n"
                                "🚀 您已成功登录，请稍后再试菜单功能。"
                            )
                        
                        # 更新用户状态
                        await state.update_data(user_data_dict)
                        
                        logger.info("User authenticated successfully", user_id=user.id)
                    else:
                        raise ValueError("No access token received")
                        
                else:
                    error_text = await response.text()
                    logger.error("Authentication failed", 
                               user_id=user.id, 
                               status=response.status, 
                               error=error_text)
                    
                    await message.answer(
                        "❌ 认证失败，请稍后重试。\n\n"
                        "如果问题持续存在，请联系客服。"
                    )
    
    except Exception as e:
        logger.error("Error in start command", user_id=user.id, error=str(e))
        await message.answer(
            "❌ 系统暂时无法响应，请稍后重试。\n\n"
            "我们的技术团队已收到通知并正在处理。"
        )


@router.message(Command("help"))
async def help_command(message: Message):
    """处理 /help 命令"""
    help_text = """
🤖 智能广告平台 Bot 使用指南

📝 **发布广告**
• 选择分类和位置
• 上传图片和描述
• 设置价格和联系方式
• 自动审核和发布

🔍 **浏览广告**
• 按分类浏览
• 关键词搜索  
• 位置筛选
• 价格区间过滤

📍 **附近广告**
• 发送位置信息
• 查看附近广告
• 距离排序

👤 **我的广告**
• 查看已发布广告
• 编辑和删除
• 查看统计数据

💬 **联系功能**
• 直接私信广告主
• 收藏感兴趣的广告
• 设置价格提醒

🛠 **常用命令**
• /start - 开始使用
• /help - 查看帮助
• /profile - 个人信息
• /settings - 设置偏好

📱 **Mini App**
• 更丰富的界面体验
• 高级搜索和筛选
• 详细广告管理
• 数据分析功能

❓ 有问题？输入 /support 联系客服
    """.strip()
    
    await message.answer(help_text)


@router.message(Command("profile"))
async def profile_command(message: Message, state: FSMContext):
    """处理 /profile 命令"""
    user_data = await state.get_data()
    
    if not user_data.get("authenticated"):
        await message.answer("❌ 请先使用 /start 命令进行认证")
        return
    
    user = message.from_user
    profile_text = f"""
👤 **个人资料**

🆔 Telegram ID: `{user.id}`
👋 姓名: {user.first_name} {user.last_name or ''}
📛 用户名: @{user.username or '未设置'}
🌐 语言: {user.language_code or 'zh'}
⭐ Telegram Premium: {'是' if user.is_premium else '否'}

📊 **使用统计**
• 发布广告: 加载中...
• 浏览次数: 加载中...
• 收藏数量: 加载中...

🛠 使用 /settings 修改偏好设置
    """.strip()
    
    await message.answer(profile_text, parse_mode="Markdown")


@router.message(Command("settings"))
async def settings_command(message: Message):
    """处理 /settings 命令"""
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
    
    await message.answer(
        "⚙️ **设置中心**\n\n请选择要修改的设置项目：",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("support"))
async def support_command(message: Message):
    """处理 /support 命令"""
    support_text = """
🎧 **客服支持**

📞 **联系我们**
• 📧 邮箱: support@adbot.com  
• 💬 在线客服: @support_bot
• 📱 客服热线: 400-123-4567
• ⏰ 服务时间: 9:00 - 21:00

❓ **常见问题**
• 如何发布广告？
• 广告审核需要多久？
• 如何修改已发布的广告？
• 如何联系广告主？

📋 **反馈建议**
• 功能建议: @feedback_bot
• Bug 报告: @bug_report_bot
• 用户体验: @ux_feedback_bot

🔧 **技术支持**
• 无法登录/注册
• 图片上传失败
• 定位功能异常
• 支付相关问题

我们会在 24 小时内回复您的问题！
    """.strip()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 联系客服", url="https://t.me/support_bot"),
            InlineKeyboardButton(text="📝 提交反馈", url="https://t.me/feedback_bot"),
        ]
    ])
    
    await message.answer(support_text, reply_markup=keyboard)


# 回调查询处理器将在 callbacks.py 中实现