#!/usr/bin/env python3
"""
商家入驻完整测试

包含完整的FSM流程和数据库集成
"""

import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from app.config import settings

# 商家入驻状态定义
class MerchantOnboardingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_region = State()
    waiting_for_address = State()
    waiting_for_contact = State()
    waiting_for_confirmation = State()

router = Router()

def get_regions_keyboard():
    """获取地区选择键盘"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏙️ 北京市", callback_data="region_1"),
            InlineKeyboardButton(text="🌃 上海市", callback_data="region_7"),
        ],
        [
            InlineKeyboardButton(text="🌆 广州市", callback_data="region_12"),
            InlineKeyboardButton(text="🏘️ 深圳市", callback_data="region_4"),
        ],
        [InlineKeyboardButton(text="🔙 取消", callback_data="cancel_onboarding")]
    ])

def get_confirmation_keyboard():
    """获取确认键盘"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_merchant"),
            InlineKeyboardButton(text="❌ 取消", callback_data="cancel_onboarding")
        ]
    ])

async def set_bot_commands(bot: Bot):
    """设置 Bot 的指令菜单"""
    commands = [
        BotCommand(command="start", description="🎆 开始使用平台"),
        BotCommand(command="merchant", description="🏪 商家管理中心"),
        BotCommand(command="help", description="ℹ️ 获取帮助"),
        BotCommand(command="about", description="📄 关于平台"),
    ]
    
    await bot.set_my_commands(commands)
    print("✅ Bot 指令菜单设置成功")


@router.message(Command("merchant"))
async def merchant_command(message: Message, state: FSMContext):
    """商家管理命令"""
    user = message.from_user
    print(f"🏪 用户 {user.id} 使用了 /merchant 命令")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 开始入驻", callback_data="become_merchant")],
        [InlineKeyboardButton(text="📋 入驻须知", callback_data="merchant_terms")],
        [InlineKeyboardButton(text="ℹ️ 帮助", callback_data="help")]
    ])
    
    await message.answer(
        "🏪 **商家管理中心**\n\n"
        "🚀 快速入驻成为认证商家\n"
        "📱 使用 Mini App 管理后台\n"
        "📊 查看实时经营数据\n"
        "💬 与客户直接沟通\n\n"
        "选择下面的操作开始吧！",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def help_command(message: Message, state: FSMContext):
    """帮助命令"""
    await message.answer(
        "ℹ️ **帮助中心**\n\n"
        "**可用指令：**\n"
        "/start - 🎆 开始使用平台\n"
        "/merchant - 🏪 商家管理中心\n"
        "/help - ℹ️ 获取帮助\n"
        "/about - 📄 关于平台\n\n"
        "**商家入驻流程：**\n"
        "1️⃣ 输入店铺名称\n"
        "2️⃣ 添加店铺描述\n"
        "3️⃣ 选择所在地区\n"
        "4️⃣ 填写详细地址\n"
        "5️⃣ 设置联系方式\n"
        "6️⃣ 确认提交\n\n"
        "**联系方式选项：**\n"
        "📱 手机号码\n"
        "💬 Telegram 用户名\n"
        "🔒 TG 匿名聊天（推荐）",
        parse_mode="Markdown"
    )


@router.message(Command("about"))
async def about_command(message: Message, state: FSMContext):
    """关于命令"""
    await message.answer(
        "📄 **关于平台**\n\n"
        "🎆 **本地服务平台**\n"
        "版本：v1.0.0\n\n"
        "📍 **产品特点：**\n"
        "• 🏪 B2C 地理位置商家服务\n"
        "• 📱 Telegram Mini App 管理后台\n"
        "• 🔒 TG 匿名聊天保护隐私\n"
        "• 📊 实时数据分析\n"
        "• 🚀 一键式商家入驻\n\n"
        "📞 **技术支持：**\n"
        "Python + FastAPI + aiogram\n"
        "React + TypeScript + Vite\n"
        "SQLite + Redis",
        parse_mode="Markdown"
    )


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """开始命令"""
    user = message.from_user
    chat_type = message.chat.type
    print(f"🚀 用户 {user.id} ({user.first_name}) 在 {chat_type} 中发送了 /start")
    
    if chat_type in ["group", "supergroup"]:
        # 群聊模式：仅显示搜索功能
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 搜索商家", callback_data="group_search"),
                InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby"),
            ],
            [
                InlineKeyboardButton(text="💬 私聊机器人", url="https://t.me/YourBotUsername"),
            ]
        ])
        
        await message.answer(
            "🔍 **群聊商家搜索**\n\n"
            "🚀 在群聊中快速搜索商家和服务\n"
            "💬 私聊机器人进行商家入驻",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # 私聊模式：完整功能
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏪 成为商家", callback_data="become_merchant")],
            [InlineKeyboardButton(text="ℹ️ 帮助", callback_data="help")]
        ])
        
        await message.answer(
            "🛍️ **本地服务平台**\n\n"
            "🚀 发现您身边的优质商家和服务\n"
            "📱 支持 Mini App 管理后台\n"
            "🔒 TG 匿名聊天保护隐私\n\n"
            "选择下面的操作开始吧！",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

@router.message(F.text.regexp(r'^[Ss]\s*(.+)'))
async def quick_search_handler(message: Message, state: FSMContext):
    """处理快速搜索：S+关键词（仅群聊）"""
    # 检查是否为群聊
    chat_type = message.chat.type
    if chat_type not in ["group", "supergroup"]:
        return  # 仅在群聊中生效
    
    text = message.text or ""
    match = re.match(r'^[Ss]\s*(.+)', text)
    
    if not match:
        return
    
    query = match.group(1).strip()
    user = message.from_user
    
    print(f"🔍 用户 {user.id} 在群聊 {message.chat.id} 中快速搜索: {query}")
    
    # 模拟搜索结果
    search_results = [
        {"name": f"{query}专家", "type": "专业服务", "rating": 4.7, "area": "附近", "distance": "200m"},
        {"name": f"优质{query}店", "type": "商业服务", "rating": 4.5, "area": "市中心", "distance": "500m"},
        {"name": f"{query}连锁店", "type": "连锁服务", "rating": 4.4, "area": "各区域", "distance": "800m"},
    ]
    
    # 生成搜索结果文本
    result_text = f"🔍 **快速搜索结果：{query}**\n\n"
    
    for i, result in enumerate(search_results, 1):
        result_text += f"{i}. **{result['name']}**\n"
        result_text += f"   📋 {result['type']} | ⭐ {result['rating']} | 📍 {result['area']}\n"
        result_text += f"   🚶 距离 {result['distance']} | 📞 私聊获取联系方式\n\n"
    
    result_text += "💡 **快速搜索技巧：**\n"
    result_text += "• 输入 `S咖啡` 搜索咖啡店\n"
    result_text += "• 输入 `S美发` 搜索美发店\n"
    result_text += "• 输入 `S维修` 搜索维修服务\n"
    result_text += "• 输入 `S会所` 搜索休闲会所\n\n"
    result_text += "💬 私聊机器人获取详细信息和联系方式"
    
    # 发送搜索结果
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 更多搜索", callback_data="group_search"),
            InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby"),
        ],
        [
            InlineKeyboardButton(text="💬 私聊获取联系方式", url="https://t.me/YourBotUsername")
        ]
    ])
    
    await message.reply(
        result_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "group_search")
async def group_search_handler(callback: CallbackQuery, state: FSMContext):
    """群聊搜索商家"""
    await callback.answer()
    
    # 模拟搜索结果
    search_results = [
        "🏪 老北京炎酱面 - 餐饮 | ⭐ 4.8 | 📍 朝阳区",
        "☕ 星巴克咖啡 - 咖啡 | ⭐ 4.6 | 📍 海淀区",
        "📱 小米之家 - 电子产品 | ⭐ 4.7 | 📍 西城区",
        "🍔 德克士 - 快餐 | ⭐ 4.3 | 📍 东城区"
    ]
    
    text = "🔍 **搜索结果**\n\n"
    for i, result in enumerate(search_results, 1):
        text += f"{i}. {result}\n"
    
    text += "\n💬 私聊机器人获取详细信息和联系方式"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 私聊机器人", url="https://t.me/YourBotUsername")],
            [InlineKeyboardButton(text="🔍 新搜索", callback_data="group_search")]
        ]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "group_nearby")
async def group_nearby_handler(callback: CallbackQuery, state: FSMContext):
    """群聊附近商家"""
    await callback.answer()
    
    # 模拟附近商家
    nearby_merchants = [
        "🏪 附近咖啡厅 - 餐饮 | ⭐ 4.6 | 🚶 50m",
        "🏪 便利店 - 购物 | ⭐ 4.3 | 🚶 120m",
        "🏪 药店 - 医疗 | ⭐ 4.5 | 🚶 200m",
        "🏪 洗衣店 - 生活服务 | ⭐ 4.4 | 🚶 300m"
    ]
    
    text = "📍 **您附近的商家**\n\n"
    for i, merchant in enumerate(nearby_merchants, 1):
        text += f"{i}. {merchant}\n"
    
    text += "\n💬 私聊机器人获取详细地址和联系方式"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 私聊机器人", url="https://t.me/YourBotUsername")],
            [InlineKeyboardButton(text="🔄 刷新", callback_data="group_nearby")]
        ]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "become_merchant")
async def start_merchant_onboarding(callback: CallbackQuery, state: FSMContext):
    """开始商家入驻流程（仅限私聊）"""
    user = callback.from_user
    chat_type = callback.message.chat.type
    
    # 检查是否为群聊
    if chat_type in ["group", "supergroup"]:
        await callback.message.edit_text(
            "❌ **商家入驻仅限私聊**\n\n"
            "🔒 为了保护您的隐私和安全，商家入驻功能仅在私聊中可用。\n\n"
            "💬 请点击下方按钮私聊机器人开始入驻：",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 私聊机器人入驻", url="https://t.me/YourBotUsername")]
            ]),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    print(f"📝 用户 {user.id} 在私聊中开始商家入驻流程")
    
    # 检查用户是否已经是商家
    try:
        conn = sqlite3.connect("./telegram_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM merchants WHERE user_id = ?", (user.id,))
        existing_merchant = cursor.fetchone()
        conn.close()
        
        if existing_merchant:
            await callback.message.edit_text(
                f"🏪 您已经是商家了！\n\n"
                f"店铺名称：{existing_merchant[1]}\n"
                f"商家ID：{existing_merchant[0]}"
            )
            await callback.answer()
            return
    except Exception as e:
        print(f"❌ 数据库查询错误: {e}")
    
    await state.set_state(MerchantOnboardingStates.waiting_for_name)
    await callback.message.edit_text(
        "🎉 欢迎入驻我们的平台！\n\n"
        "第一步：请输入您的店铺名称\n"
        "💡 建议：使用简洁明了、容易记住的名称"
    )
    await callback.answer()

@router.message(MerchantOnboardingStates.waiting_for_name)
async def process_merchant_name(message: Message, state: FSMContext):
    """处理店铺名称输入"""
    name = message.text.strip() if message.text else ""
    user = message.from_user
    
    print(f"📝 用户 {user.id} 输入店铺名称: {name}")
    
    if len(name) < 2:
        await message.answer("❌ 店铺名称至少需要2个字符，请重新输入：")
        return
    
    if len(name) > 50:
        await message.answer("❌ 店铺名称不能超过50个字符，请重新输入：")
        return
    
    await state.update_data(name=name)
    await state.set_state(MerchantOnboardingStates.waiting_for_description)
    await message.answer(
        f"✅ 店铺名称：{name}\n\n"
        "第二步：请用简短的话介绍您的店铺\n"
        "💡 例如：主营什么产品/服务，有什么特色等\n"
        "(可以发送'跳过'来暂时不填写)"
    )

@router.message(MerchantOnboardingStates.waiting_for_description)
async def process_merchant_description(message: Message, state: FSMContext):
    """处理店铺描述输入"""
    description = message.text.strip() if message.text else ""
    user = message.from_user
    
    print(f"📝 用户 {user.id} 输入店铺描述: {description}")
    
    if description.lower() in ["跳过", "skip", "无", "不填"]:
        description = None
    elif len(description) > 500:
        await message.answer("❌ 店铺描述不能超过500个字符，请重新输入或发送'跳过'：")
        return
    
    await state.update_data(description=description)
    await state.set_state(MerchantOnboardingStates.waiting_for_region)
    await message.answer(
        "✅ 店铺描述已保存\n\n"
        "第三步：请选择您的店铺所在地区：",
        reply_markup=get_regions_keyboard()
    )

@router.callback_query(F.data.startswith("region_"), MerchantOnboardingStates.waiting_for_region)
async def process_region_selection(callback: CallbackQuery, state: FSMContext):
    """处理地区选择"""
    region_id = int(callback.data.split("_")[1])
    user = callback.from_user
    
    region_names = {1: "北京市", 7: "上海市", 12: "广州市", 4: "深圳市"}
    region_name = region_names.get(region_id, "未知地区")
    
    print(f"📍 用户 {user.id} 选择地区: {region_name} (ID: {region_id})")
    
    await state.update_data(region_id=region_id, region_name=region_name)
    await state.set_state(MerchantOnboardingStates.waiting_for_address)
    
    await callback.message.edit_text(
        f"✅ 已选择地区：{region_name}\n\n"
        "第四步：请输入您的详细地址\n"
        "💡 包括街道、门牌号等，方便客户找到您\n"
        "(可以发送'跳过'来暂时不填写)"
    )
    await callback.answer()

@router.message(MerchantOnboardingStates.waiting_for_address)
async def process_merchant_address(message: Message, state: FSMContext):
    """处理详细地址输入"""
    address = message.text.strip() if message.text else ""
    user = message.from_user
    
    print(f"📍 用户 {user.id} 输入地址: {address}")
    
    if address.lower() in ["跳过", "skip", "无", "不填"]:
        address = None
    elif len(address) > 200:
        await message.answer("❌ 地址不能超过200个字符，请重新输入或发送'跳过'：")
        return
    
    await state.update_data(address=address)
    await state.set_state(MerchantOnboardingStates.waiting_for_contact)
    await message.answer(
        "✅ 地址信息已保存\n\n"
        "第五步：请选择联系方式\n\n"
        "📱 手机号码：13800138000\n"
        "💬 Telegram用户名：@username\n"
        "🚀 或发送'跳过'使用TG匿名聊天\n\n"
        "🔒 TG匿名聊天：客户可直接通过Bot与您沟通，保护双方隐私"
    )

@router.message(MerchantOnboardingStates.waiting_for_contact)
async def process_merchant_contact(message: Message, state: FSMContext):
    """处理联系方式输入"""
    contact = message.text.strip() if message.text else ""
    user = message.from_user
    
    print(f"📱 用户 {user.id} 输入联系方式: {contact}")
    
    # 支持多种格式的联系方式
    if contact.lower() in ["跳过", "skip", "无", "不填"]:
        # 默认使用TG匿名聊天
        await state.update_data(
            contact_phone=None,
            contact_telegram=f"@{user.username}" if user.username else f"tg://user?id={user.id}",
            contact_method="telegram"
        )
        contact_display = "Telegram 匿名聊天"
    elif contact.isdigit() and len(contact) == 11:
        # 手机号码
        await state.update_data(
            contact_phone=contact,
            contact_telegram=f"@{user.username}" if user.username else f"tg://user?id={user.id}",
            contact_method="phone"
        )
        contact_display = f"手机号: {contact}"
    elif contact.startswith("@") and len(contact) > 1:
        # Telegram 用户名
        await state.update_data(
            contact_phone=None,
            contact_telegram=contact,
            contact_method="telegram"
        )
        contact_display = f"Telegram: {contact}"
    else:
        await message.answer(
            "❌ 请输入正确的联系方式：\n\n"
            "📱 手机号码：13800138000\n"
            "💬 Telegram：@username\n"
            "🚀 或发送'跳过'使用TG匿名聊天"
        )
        return
    
    # 显示确认信息
    user_data = await state.get_data()
    confirmation_text = "🔍 请确认您的店铺信息：\n\n"
    confirmation_text += f"🏪 店铺名称：{user_data['name']}\n"
    
    if user_data.get('description'):
        confirmation_text += f"📄 店铺描述：{user_data['description']}\n"
    
    confirmation_text += f"📍 所在地区：{user_data['region_name']}\n"
    
    if user_data.get('address'):
        confirmation_text += f"🏠 详细地址：{user_data['address']}\n"
    
    confirmation_text += f"📱 联系方式：{contact_display}\n"
    
    # 添加TG匿名聊天说明
    if user_data.get('contact_method') == 'telegram':
        confirmation_text += "🔒 客户可通过Bot与您匿名沟通\n"
    
    confirmation_text += "\n✨ 入驻后您将获得免费版商家账户"
    
    await state.set_state(MerchantOnboardingStates.waiting_for_confirmation)
    await message.answer(confirmation_text, reply_markup=get_confirmation_keyboard())

@router.callback_query(F.data == "confirm_merchant", MerchantOnboardingStates.waiting_for_confirmation)
async def confirm_merchant_creation(callback: CallbackQuery, state: FSMContext):
    """确认创建商家"""
    user = callback.from_user
    user_data = await state.get_data()
    
    print(f"✅ 用户 {user.id} 确认创建商家，开始写入数据库...")
    
    try:
        # 写入数据库
        conn = sqlite3.connect("./telegram_bot.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO merchants (
                user_id, name, description, region_id, address, 
                contact_phone, contact_telegram, subscription_tier, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'free', 'active')
        """, (
            user.id,
            user_data['name'],
            user_data.get('description'),
            user_data['region_id'],
            user_data.get('address'),
            user_data.get('contact_phone'),
            user_data.get('contact_telegram')
        ))
        
        merchant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"🎉 商家创建成功! 商家ID: {merchant_id}")
        
        # 根据联系方式显示不同信息
        contact_info = ""
        if user_data.get('contact_method') == 'telegram':
            contact_info = "🔒 客户可通过Bot与您匿名沟通"
        elif user_data.get('contact_phone'):
            contact_info = f"📱 联系电话：{user_data['contact_phone']}"
        
        await callback.message.edit_text(
            "🎉 恭喜！您的店铺已成功创建！\n\n"
            f"🏪 店铺名称：{user_data['name']}\n"
            f"📊 订阅状态：免费版\n"
            f"🆔 商家ID：{merchant_id}\n"
            f"{contact_info}\n\n"
            "✅ 您现在可以：\n"
            "• 发布商品和服务\n"
            "• 管理客户询盘\n"
            "• 查看店铺数据\n\n"
            "💡 升级到专业版可获得更多功能！",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 管理后台(React)", web_app={"url": "https://cold-snails-return.loca.lt"})],
                [InlineKeyboardButton(text="🧪 基础测试页面", web_app={"url": "https://cold-snails-return.loca.lt/test.html"})],
                [InlineKeyboardButton(text="📦 继续测试", callback_data="become_merchant")]
            ])
        )
        
        # 清理状态
        await state.clear()
        
    except Exception as e:
        print(f"❌ 数据库写入错误: {e}")
        await callback.message.edit_text(
            "❌ 系统繁忙，请稍后再试。\n"
            "如果问题持续，请联系客服。"
        )
    
    await callback.answer()

@router.callback_query(F.data == "cancel_onboarding")
async def cancel_onboarding(callback: CallbackQuery, state: FSMContext):
    """取消入驻流程"""
    user = callback.from_user
    print(f"❌ 用户 {user.id} 取消了商家入驻流程")
    
    await state.clear()
    await callback.message.edit_text(
        "❌ 已取消商家入驻流程\n\n"
        "您可以随时重新开始入驻！"
    )
    await callback.answer()

async def main():
    """主函数"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # 设置 Bot 指令菜单
    await set_bot_commands(bot)
    
    print("🚀 商家入驻测试Bot启动...")
    print("📋 支持的功能:")
    print("  - /start 命令")
    print("  - /merchant 商家管理")
    print("  - /help 帮助")
    print("  - /about 关于")
    print("  - 完整的6步商家入驻流程")
    print("  - 数据库集成")
    print("  - FSM状态管理")
    print("  - Mini App 管理后台")
    print("-" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())