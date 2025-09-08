"""
群聊商家搜索处理器

专门处理群聊中的商家搜索功能
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.core.logging import get_logger

logger = get_logger(__name__)
router = Router()


class GroupSearchStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_location = State()


@router.message(F.text.regexp(r'^[Ss]\s*(.+)'))
async def quick_search_handler(message: Message, state: FSMContext):
    """处理快速搜索：S+关键词"""
    # 检查是否为群聊
    chat_type = message.chat.type
    if chat_type not in ["group", "supergroup"]:
        return  # 仅在群聊中生效
    
    import re
    text = message.text or ""
    match = re.match(r'^[Ss]\s*(.+)', text)
    
    if not match:
        return
    
    query = match.group(1).strip()
    user = message.from_user
    
    logger.info(f"🔍 用户 {user.id} 在群聊 {message.chat.id} 中快速搜索: {query}")
    
    # 模拟搜索结果
    search_results = [
        {"name": f"{query}专家", "type": "专业服务", "rating": 4.7, "area": "附近", "phone": "138****5678"},
        {"name": f"优质{query}店", "type": "商业服务", "rating": 4.5, "area": "市中心", "phone": "139****9999"},
        {"name": f"{query}连锁店", "type": "连锁服务", "rating": 4.4, "area": "各区域", "phone": "400-****-888"},
    ]
    
    # 生成搜索结果文本
    result_text = f"🔍 **快速搜索结果：{query}**\n\n"
    
    for i, result in enumerate(search_results, 1):
        result_text += f"{i}. **{result['name']}**\n"
        result_text += f"   📋 {result['type']} | ⭐ {result['rating']} | 📍 {result['area']}\n"
        result_text += f"   📞 {result['phone']}\n\n"
    
    result_text += "💡 **快速搜索技巧：**\n"
    result_text += "• 输入 `S咖啡` 搜索咖啡店\n"
    result_text += "• 输入 `S美发` 搜索美发店\n"
    result_text += "• 输入 `S维修` 搜索维修服务\n\n"
    result_text += "💬 私聊机器人获取更多详细信息"
    
    # 发送搜索结果
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 更多搜索", callback_data="group_search_merchants"),
            InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby_merchants"),
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


@router.callback_query(F.data == "group_search_merchants")
async def group_search_merchants(callback: CallbackQuery, state: FSMContext):
    """群聊中搜索商家"""
    await callback.answer()
    
    chat_type = callback.message.chat.type
    if chat_type not in ["group", "supergroup"]:
        await callback.message.edit_text("❌ 此功能仅在群聊中可用")
        return
    
    await state.set_state(GroupSearchStates.waiting_for_search_query)
    await callback.message.edit_text(
        "🔍 **群聊商家搜索**\n\n"
        "请输入您要搜索的内容：\n"
        "💡 例如：\n"
        "• 火锅\n"
        "• 咖啡店\n"
        "• 美发店\n"
        "• 维修服务\n\n"
        "输入 /cancel 取消搜索",
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "group_nearby_merchants")
async def group_nearby_merchants(callback: CallbackQuery, state: FSMContext):
    """群聊中搜索附近商家"""
    await callback.answer()
    
    chat_type = callback.message.chat.type
    if chat_type not in ["group", "supergroup"]:
        await callback.message.edit_text("❌ 此功能仅在群聊中可用")
        return
    
    await state.set_state(GroupSearchStates.waiting_for_location)
    await callback.message.edit_text(
        "📍 **附近商家搜索**\n\n"
        "请发送您的位置信息，我将为您查找附近的商家：\n\n"
        "📱 点击下方按钮或发送位置",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📍 发送位置", request_location=True)],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_group_search")]
        ]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "group_choose_region")
async def group_choose_region(callback: CallbackQuery, state: FSMContext):
    """群聊中选择地区"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🌏 **选择地区**\n\n"
        "请选择您要查看的地区：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏙️ 北京市", callback_data="group_region_1"),
                InlineKeyboardButton(text="🌃 上海市", callback_data="group_region_7"),
            ],
            [
                InlineKeyboardButton(text="🌆 广州市", callback_data="group_region_12"),
                InlineKeyboardButton(text="🏘️ 深圳市", callback_data="group_region_4"),
            ],
            [
                InlineKeyboardButton(text="🔙 返回", callback_data="back_to_group_main")
            ]
        ]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "group_popular_merchants")
async def group_popular_merchants(callback: CallbackQuery, state: FSMContext):
    """群聊中显示热门商家"""
    await callback.answer()
    
    # 模拟热门商家数据
    popular_merchants = [
        {"name": "老北京炸酱面", "type": "餐饮", "rating": 4.8, "area": "朝阳区"},
        {"name": "星巴克咖啡", "type": "咖啡", "rating": 4.6, "area": "海淀区"},
        {"name": "小米之家", "type": "电子产品", "rating": 4.7, "area": "西城区"},
        {"name": "德克士", "type": "快餐", "rating": 4.3, "area": "东城区"},
    ]
    
    text = "🔥 **热门商家推荐**\n\n"
    for i, merchant in enumerate(popular_merchants, 1):
        text += f"{i}. **{merchant['name']}**\n"
        text += f"   📋 {merchant['type']} | ⭐ {merchant['rating']} | 📍 {merchant['area']}\n\n"
    
    text += "💡 私聊机器人获取更多详细信息和联系方式"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 搜索更多", callback_data="group_search_merchants"),
                InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby_merchants"),
            ],
            [InlineKeyboardButton(text="🔙 返回", callback_data="back_to_group_main")]
        ]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("group_region_"))
async def group_region_selected(callback: CallbackQuery, state: FSMContext):
    """群聊中选择了特定地区"""
    await callback.answer()
    
    region_id = callback.data.split("_")[-1]
    region_names = {
        "1": "北京市",
        "7": "上海市", 
        "12": "广州市",
        "4": "深圳市"
    }
    
    region_name = region_names.get(region_id, "未知地区")
    
    # 模拟该地区的商家
    merchants = [
        {"name": f"{region_name}美食城", "type": "餐饮", "rating": 4.5},
        {"name": f"{region_name}便民超市", "type": "购物", "rating": 4.3},
        {"name": f"{region_name}理发店", "type": "美容", "rating": 4.6},
    ]
    
    text = f"📍 **{region_name}商家推荐**\n\n"
    for i, merchant in enumerate(merchants, 1):
        text += f"{i}. **{merchant['name']}**\n"
        text += f"   📋 {merchant['type']} | ⭐ {merchant['rating']}\n\n"
    
    text += "💡 私聊机器人获取更多详细信息和联系方式"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回", callback_data="group_choose_region")]
        ]),
        parse_mode="Markdown"
    )


@router.message(GroupSearchStates.waiting_for_search_query)
async def process_group_search_query(message: Message, state: FSMContext):
    """处理群聊搜索查询"""
    query = message.text.strip() if message.text else ""
    
    if not query:
        await message.answer("❌ 请输入搜索内容")
        return
    
    if query.lower() in ["/cancel", "取消"]:
        await state.clear()
        await message.answer("❌ 搜索已取消")
        return
    
    # 模拟搜索结果
    search_results = [
        {"name": f"{query}专卖店", "type": "专业服务", "rating": 4.7, "area": "附近"},
        {"name": f"优质{query}店", "type": "商业服务", "rating": 4.5, "area": "市中心"},
        {"name": f"{query}连锁店", "type": "连锁服务", "rating": 4.4, "area": "各区域"},
    ]
    
    # 生成搜索结果文本
    result_text = f"🔍 **搜索结果：{query}**\n\n"
    
    for i, result in enumerate(search_results, 1):
        result_text += f"{i}. **{result['name']}**\n"
        result_text += f"   📋 {result['type']} | ⭐ {result['rating']} | 📍 {result['area']}\n\n"
    
    result_text += "💬 私聊机器人获取更多详细信息和联系方式"
    
    # 发送搜索结果
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 重新搜索", callback_data="group_search_merchants"),
            InlineKeyboardButton(text="📍 附近商家", callback_data="group_nearby_merchants"),
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
    
    # 清除状态
    await state.clear()


@router.message(GroupSearchStates.waiting_for_location)
async def process_group_location(message: Message, state: FSMContext):
    """处理群聊位置信息"""
    if not message.location:
        await message.answer("❌ 请发送位置信息或点击下方按钮")
        return
    
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    # 模拟附近商家
    nearby_merchants = [
        {"name": "附近咖啡厅", "type": "餐饮", "rating": 4.6, "distance": "50m"},
        {"name": "便利店", "type": "购物", "rating": 4.3, "distance": "120m"},
        {"name": "药店", "type": "医疗", "rating": 4.5, "distance": "200m"},
        {"name": "洗衣店", "type": "生活服务", "rating": 4.4, "distance": "300m"},
    ]
    
    text = f"📍 **您附近的商家** (位置: {latitude:.4f}, {longitude:.4f})\n\n"
    for i, merchant in enumerate(nearby_merchants, 1):
        text += f"{i}. **{merchant['name']}**\n"
        text += f"   📋 {merchant['type']} | ⭐ {merchant['rating']} | 🚶 {merchant['distance']}\n\n"
    
    text += "💬 私聊机器人获取更多详细信息和联系方式"
    
    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 刷新", callback_data="group_nearby_merchants"),
                InlineKeyboardButton(text="💬 私聊机器人", url="https://t.me/YourBotUsername")
            ]
        ]),
        parse_mode="Markdown"
    )
    
    # 清除状态
    await state.clear()


@router.callback_query(F.data == "cancel_group_search")
async def cancel_group_search(callback: CallbackQuery, state: FSMContext):
    """取消群聊搜索"""
    await state.clear()
    await callback.message.edit_text("❌ 搜索已取消")
    await callback.answer()