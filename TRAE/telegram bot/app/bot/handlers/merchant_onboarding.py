"""
商家入驻流程处理器

实现完整的商家入驻有限状态机
"""

from typing import Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import httpx
import json

from app.bot.states.merchant_states import MerchantOnboardingStates
from app.config import settings

router = Router()

# 地区选择键盘
def get_regions_keyboard():
    """获取地区选择键盘"""
    regions = [
        {"id": 1, "name": "北京市"},
        {"id": 2, "name": "上海市"},
        {"id": 3, "name": "广州市"},
        {"id": 4, "name": "深圳市"},
        {"id": 5, "name": "杭州市"},
        {"id": 6, "name": "成都市"},
    ]
    
    keyboard = []
    for i in range(0, len(regions), 2):
        row = []
        for j in range(i, min(i + 2, len(regions))):
            region = regions[j]
            row.append(InlineKeyboardButton(
                text=region["name"],
                callback_data=f"region_{region['id']}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 返回", callback_data="cancel_onboarding")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard():
    """获取确认键盘"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 确认提交", callback_data="confirm_merchant"),
            InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_merchant")
        ],
        [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_onboarding")]
    ])


@router.callback_query(F.data == "start_merchant_onboarding")
async def start_merchant_onboarding(callback: CallbackQuery, state: FSMContext):
    """开始商家入驻流程"""
    await state.set_state(MerchantOnboardingStates.entering_name)
    if callback.message:
        await callback.message.edit_text(
            "🎉 欢迎入驻我们的平台！\n\n"
            "第一步：请输入您的店铺名称\n"
            "💡 建议：使用简洁明了、容易记住的名称"
        )
    await callback.answer()


@router.message(StateFilter(MerchantOnboardingStates.entering_name))
async def process_merchant_name(message: Message, state: FSMContext):
    """处理店铺名称输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ 店铺名称至少需要2个字符，请重新输入：")
        return
    
    if len(name) > 50:
        await message.answer("❌ 店铺名称不能超过50个字符，请重新输入：")
        return
    
    await state.update_data(name=name)
    await state.set_state(MerchantOnboardingStates.entering_description)
    await message.answer(
        f"✅ 店铺名称：{name}\n\n"
        "第二步：请用简短的话介绍您的店铺\n"
        "💡 例如：主营什么产品/服务，有什么特色等\n"
        "(可以发送'跳过'来暂时不填写)"
    )


@router.message(StateFilter(MerchantOnboardingStates.entering_description))
async def process_merchant_description(message: Message, state: FSMContext):
    """处理店铺描述输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    description = message.text.strip()
    
    if description.lower() in ["跳过", "skip", "无", "不填"]:
        description = None
    elif len(description) > 500:
        await message.answer("❌ 店铺描述不能超过500个字符，请重新输入或发送'跳过'：")
        return
    
    await state.update_data(description=description)
    await state.set_state(MerchantOnboardingStates.choosing_region)
    await message.answer(
        "✅ 店铺描述已保存\n\n"
        "第三步：请选择您的店铺所在地区：",
        reply_markup=get_regions_keyboard()
    )


@router.callback_query(F.data.startswith("region_"), StateFilter(MerchantOnboardingStates.choosing_region))
async def process_region_selection(callback: CallbackQuery, state: FSMContext):
    """处理地区选择"""
    if not callback.data:
        return
        
    region_id = int(callback.data.split("_")[1])
    
    region_names = {
        1: "北京市", 2: "上海市", 3: "广州市",
        4: "深圳市", 5: "杭州市", 6: "成都市"
    }
    
    region_name = region_names.get(region_id, "未知地区")
    await state.update_data(region_id=region_id, region_name=region_name)
    
    await state.set_state(MerchantOnboardingStates.entering_address)
    if callback.message:
        await callback.message.edit_text(
            f"✅ 已选择地区：{region_name}\n\n"
            "第四步：请输入您的详细地址\n"
            "💡 包括街道、门牌号等，方便客户找到您\n"
            "(可以发送'跳过'来暂时不填写)"
        )
    await callback.answer()


@router.message(StateFilter(MerchantOnboardingStates.entering_address))
async def process_merchant_address(message: Message, state: FSMContext):
    """处理详细地址输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    address = message.text.strip()
    
    if address.lower() in ["跳过", "skip", "无", "不填"]:
        address = None
    elif len(address) > 200:
        await message.answer("❌ 地址不能超过200个字符，请重新输入或发送'跳过'：")
        return
    
    await state.update_data(address=address)
    await state.set_state(MerchantOnboardingStates.entering_contact)
    await message.answer(
        "✅ 地址信息已保存\n\n"
        "第五步：请选择联系方式\n\n"
        "📱 手机号码：13800138000\n"
        "💬 Telegram用户名：@username\n"
        "🚀 或发送'跳过'使用TG匿名聊天\n\n"
        "🔒 TG匿名聊天：客户可直接通过Bot与您沟通，保护双方隐私"
    )


@router.message(StateFilter(MerchantOnboardingStates.entering_contact))
async def process_merchant_contact(message: Message, state: FSMContext):
    """处理联系方式输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    contact = message.text.strip()
    user = message.from_user
    
    # 支持多种格式的联系方式
    if contact.lower() in ["跳过", "skip", "无", "不填"]:
        # 默认使用TG匿名聊天
        telegram_contact = f"@{user.username}" if user and user.username else f"tg://user?id={user.id if user else 0}"
        await state.update_data(
            contact_phone=None,
            contact_telegram=telegram_contact,
            contact_method="telegram"
        )
        contact_display = "🔒 TG匿名聊天"
    elif contact.isdigit() and len(contact) == 11:
        # 手机号码
        telegram_contact = f"@{user.username}" if user and user.username else f"tg://user?id={user.id if user else 0}"
        await state.update_data(
            contact_phone=contact,
            contact_telegram=telegram_contact,
            contact_method="phone"
        )
        contact_display = f"📱 手机号: {contact}"
    elif contact.startswith("@") and len(contact) > 1:
        # Telegram 用户名
        await state.update_data(
            contact_phone=None,
            contact_telegram=contact,
            contact_method="telegram"
        )
        contact_display = f"💬 Telegram: {contact}"
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
    if user_data.get('contact_method') == 'telegram' and user_data.get('contact_phone') is None:
        confirmation_text += "🔒 客户可通过Bot与您匿名沟通\n"
    
    confirmation_text += "\n✨ 入驻后您将获得免费版商家账户"
    
    await state.set_state(MerchantOnboardingStates.confirming_onboarding)
    await message.answer(confirmation_text, reply_markup=get_confirmation_keyboard())


@router.callback_query(F.data == "confirm_merchant", StateFilter(MerchantOnboardingStates.confirming_onboarding))
async def confirm_merchant_creation(callback: CallbackQuery, state: FSMContext):
    """确认创建商家"""
    user_data = await state.get_data()
    
    # 调用API创建商家
    try:
        async with httpx.AsyncClient() as client:
            # 准备商家数据
            merchant_data = {
                "name": user_data['name'],
                "description": user_data.get('description'),
                "region_id": user_data['region_id'],
                "address": user_data.get('address'),
                "contact_phone": user_data.get('contact_phone'),
                "contact_telegram": user_data.get('contact_telegram')
            }
            
            # 获取用户认证信息（从状态中获取）
            auth_data = await state.get_data()
            access_token = auth_data.get("access_token")
            
            if not access_token:
                raise Exception("未找到访问令牌")
            
            # 调用API创建商家
            response = await client.post(
                f"{settings.API_BASE_URL}/api/v1/merchants/",
                json=merchant_data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 201:
                api_response = response.json()
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ 创建商家时发生错误，请稍后重试或联系客服。\n错误详情: {str(e)}"
            )
        await state.clear()
        await callback.answer()
        return
    
    # 根据联系方式类型生成不同的成功消息
    contact_info = ""
    if user_data.get('contact_method') == 'phone':
        contact_info = f"📱 联系电话：{user_data['contact_phone']}"
    elif user_data.get('contact_method') == 'telegram':
        if user_data.get('contact_telegram', '').startswith('@'):
            contact_info = f"💬 TG联系：{user_data['contact_telegram']}"
        else:
            contact_info = "🔒 TG匿名聊天：客户可直接通过平台联系您"
    
    # 将用户状态设置为商家
    await state.update_data(is_merchant=True)
    
    if callback.message:
        await callback.message.edit_text(
            "🎉 恭喜！您的店铺已成功创建！\n\n"
            f"🏪 店铺名称：{user_data['name']}\n"
            f"{contact_info}\n"
            f"📊 订阅状态：免费版\n\n"
            "✅ 您现在可以：\n"
            "• 发布商品和服务\n"
            "• 管理客户询盘\n"
            "• 查看店铺数据\n\n"
            "💡 升级到专业版可获得更多功能！",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 打开管理后台", web_app={"url": "https://cold-snails-return.loca.lt"})],
                [InlineKeyboardButton(text="🏪 商家管理中心", callback_data="back_to_main")],
                [InlineKeyboardButton(text="📦 发布第一个商品", callback_data="add_product")]
            ])
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_onboarding")
async def cancel_onboarding(callback: CallbackQuery, state: FSMContext):
    """取消入驻流程"""
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            "❌ 已取消商家入驻流程\n\n"
            "您可以随时重新开始入驻！"
        )
    await callback.answer()