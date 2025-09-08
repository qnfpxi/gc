#!/usr/bin/env python3
"""
简化的 /start 命令测试

绕过API调用，直接测试菜单显示功能
"""

import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from app.config import settings

router = Router()

@router.message(Command("start"))
async def simple_start(message: Message, state: FSMContext):
    """简化的start命令 - 直接显示菜单"""
    try:
        user = message.from_user
        print(f"收到 /start 命令 - 用户: {user.id} ({user.first_name})")
        
        # 直接显示消费者菜单
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
                InlineKeyboardButton(text="🏪 成为商家", callback_data="become_merchant"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ 帮助", callback_data="help"),
            ],
        ])
        
        await message.answer(
            text, 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )
        
        print(f"✅ 菜单发送成功 - 用户: {user.id}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        await message.answer("❌ 出现错误，请重试")

@router.callback_query(F.data == "become_merchant")
async def simple_become_merchant(callback, state: FSMContext):
    """简化的成为商家功能"""
    await callback.answer()
    await callback.message.edit_text(
        "🏪 **商家入驻**\\n\\n"
        "欢迎加入我们的平台！",
        parse_mode="Markdown"
    )

async def main():
    """主函数"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 简化测试Bot启动...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())