"""
商品管理处理器

实现商家商品的创建、编辑、删除和展示功能
"""

from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import httpx

from app.bot.states.merchant_states import ProductManagementStates
from app.config import settings

router = Router()


# 商品分类
PRODUCT_CATEGORIES = [
    {"id": 1, "name": "餐饮美食"},
    {"id": 2, "name": "生活服务"},
    {"id": 3, "name": "教育培训"},
    {"id": 4, "name": "美容美发"},
    {"id": 5, "name": "休闲娱乐"},
    {"id": 6, "name": "购物零售"},
    {"id": 7, "name": "交通出行"},
    {"id": 8, "name": "医疗健康"},
]


async def upload_image_to_api(bot, file, access_token: str) -> Optional[str]:
    """上传图片到API并返回URL"""
    try:
        # 获取文件信息
        file_info = await bot.get_file(file.file_id)
        file_path = file_info.file_path
        
        # 下载文件
        file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
        
        # 上传到我们的API
        async with httpx.AsyncClient() as client:
            # 首先下载文件
            file_response = await client.get(file_url)
            if file_response.status_code != 200:
                return None
                
            # 然后上传到我们的API
            files = {
                'file': (file.file_id, file_response.content, 'image/jpeg')
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            api_response = await client.post(
                f"{settings.API_BASE_URL}/api/v1/upload/image",
                files=files,
                headers=headers
            )
            
            if api_response.status_code == 200:
                return api_response.json().get('url')
            return None
    except Exception as e:
        print(f"上传图片失败: {e}")
        return None


def get_categories_keyboard():
    """获取商品分类键盘"""
    keyboard = []
    for i in range(0, len(PRODUCT_CATEGORIES), 2):
        row = []
        for j in range(i, min(i + 2, len(PRODUCT_CATEGORIES))):
            category = PRODUCT_CATEGORIES[j]
            row.append(InlineKeyboardButton(
                text=category["name"],
                callback_data=f"product_category_{category['id']}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 返回", callback_data="cancel_product_creation")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard():
    """获取确认键盘"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 确认发布", callback_data="confirm_product"),
            InlineKeyboardButton(text="✏️ 重新编辑", callback_data="edit_product")
        ],
        [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
    ])


@router.callback_query(F.data == "add_product")
async def start_product_creation(callback: CallbackQuery, state: FSMContext):
    """开始商品创建流程"""
    await state.set_state(ProductManagementStates.choosing_product_category)
    if callback.message:
        await callback.message.edit_text(
            "🎉 发布新商品\n\n"
            "第一步：请选择商品分类"
        )
        await callback.message.edit_reply_markup(reply_markup=get_categories_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("product_category_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """处理商品分类选择"""
    if not callback.data:
        return
        
    category_id = int(callback.data.split("_")[-1])
    
    category_name = next((cat["name"] for cat in PRODUCT_CATEGORIES if cat["id"] == category_id), "未知分类")
    await state.update_data(category_id=category_id, category_name=category_name)
    
    await state.set_state(ProductManagementStates.entering_product_name)
    if callback.message:
        await callback.message.edit_text(
            f"✅ 已选择分类：{category_name}\n\n"
            "第二步：请输入商品名称\n"
            "💡 建议：简洁明了，突出商品特点"
        )
        await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 返回", callback_data="add_product")]
        ]))
    await callback.answer()


@router.message(ProductManagementStates.entering_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """处理商品名称输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ 商品名称至少需要2个字符，请重新输入：")
        return
    
    if len(name) > 50:
        await message.answer("❌ 商品名称不能超过50个字符，请重新输入：")
        return
    
    await state.update_data(name=name)
    await state.set_state(ProductManagementStates.entering_product_description)
    await message.answer(
        f"✅ 商品名称：{name}\n\n"
        "第三步：请输入商品描述\n"
        "💡 详细介绍商品特点、规格、使用方法等\n"
        "(可以发送'跳过'来暂时不填写)"
    )


@router.message(ProductManagementStates.entering_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """处理商品描述输入"""
    if not message.text:
        await message.answer("❌ 请输入文字内容：")
        return
        
    description = message.text.strip()
    
    if description.lower() in ["跳过", "skip", "无", "不填"]:
        description = None
    elif len(description) > 500:
        await message.answer("❌ 商品描述不能超过500个字符，请重新输入或发送'跳过'：")
        return
    
    await state.update_data(description=description)
    await state.set_state(ProductManagementStates.setting_product_price)
    await message.answer(
        "✅ 商品描述已保存\n\n"
        "第四步：请输入商品价格\n"
        "💡 格式：数字（元）\n"
        "例如：29.9 或 199"
    )


@router.message(ProductManagementStates.setting_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """处理商品价格输入"""
    if not message.text:
        await message.answer("❌ 请输入价格：")
        return
        
    price_text = message.text.strip()
    
    try:
        # 尝试解析价格
        if price_text.lower() in ["跳过", "skip", "无", "不填"]:
            price = None
        else:
            price = float(price_text)
            if price < 0:
                raise ValueError("价格不能为负数")
    except ValueError:
        await message.answer("❌ 请输入正确的价格格式（数字），例如：29.9 或 199\n或发送'跳过'：")
        return
    
    await state.update_data(price=price)
    await state.set_state(ProductManagementStates.adding_product_tags)
    await message.answer(
        "✅ 商品价格已保存\n\n"
        "第五步：请输入商品标签\n"
        "💡 用逗号分隔多个标签，例如：新品,热销,优惠\n"
        "(可以发送'跳过'来暂时不填写)"
    )


@router.message(ProductManagementStates.adding_product_tags)
async def process_product_tags(message: Message, state: FSMContext):
    """处理商品标签输入"""
    if not message.text:
        await message.answer("❌ 请输入标签：")
        return
        
    tags_text = message.text.strip()
    
    if tags_text.lower() in ["跳过", "skip", "无", "不填"]:
        tags = []
    else:
        # 分割标签并清理
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        # 限制标签数量和长度
        tags = tags[:10]  # 最多10个标签
        tags = [tag[:20] for tag in tags]  # 每个标签最多20字符
    
    await state.update_data(tags=tags)
    
    await state.set_state(ProductManagementStates.uploading_product_images)
    await message.answer(
        "✅ 商品标签已保存\n\n"
        "🖼️ 请上传商品图片\n"
        "• 最多可上传5张图片\n"
        "• 支持 JPG、PNG、WebP 格式\n"
        "• 每张图片不超过10MB\n\n"
        "请发送第一张图片，或点击「跳过」继续：",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ 跳过图片", callback_data="skip_product_images")],
            [InlineKeyboardButton(text="🔙 修改标签", callback_data="edit_product_tags")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
        ])
    )


@router.message(ProductManagementStates.uploading_product_images, F.photo)
async def process_product_image_upload(message: Message, state: FSMContext):
    """处理商品图片上传"""
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
            product_data = data.get("product_data", {})
            images = product_data.get("images", [])
            images.append(image_url)
            product_data["images"] = images
            await state.update_data(product_data=product_data)
            
            await processing_msg.delete()
            
            images_count = len(images)
            keyboard = []
            
            if images_count < 5:
                keyboard.append([InlineKeyboardButton(text="📸 添加更多图片", callback_data="add_more_product_images")])
            
            keyboard.extend([
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="product_images_done")],
                [InlineKeyboardButton(text="🗑 删除最后一张", callback_data="delete_last_product_image")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
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
        logger.error("Error uploading product image", error=str(e))
        await message.answer("❌ 图片处理失败，请重试或跳过此步骤。")


@router.callback_query(ProductManagementStates.uploading_product_images, F.data == "skip_product_images")
async def skip_product_images(callback: CallbackQuery, state: FSMContext):
    """跳过商品图片上传"""
    await callback.answer()
    await show_product_confirmation(callback.message, state)


@router.callback_query(ProductManagementStates.uploading_product_images, F.data == "add_more_product_images")
async def add_more_product_images(callback: CallbackQuery, state: FSMContext):
    """添加更多商品图片"""
    await callback.answer()
    await callback.message.edit_text(
        "📸 请继续发送图片，最多还可以上传 {} 张图片。".format(
            5 - len((await state.get_data()).get("product_data", {}).get("images", []))
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ 图片完成", callback_data="product_images_done")],
            [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
        ])
    )


@router.callback_query(ProductManagementStates.uploading_product_images, F.data == "delete_last_product_image")
async def delete_last_product_image(callback: CallbackQuery, state: FSMContext):
    """删除最后一张商品图片"""
    await callback.answer()
    
    # 获取当前图片列表
    data = await state.get_data()
    product_data = data.get("product_data", {})
    images = product_data.get("images", [])
    
    if images:
        # 删除最后一张图片
        deleted_image = images.pop()
        product_data["images"] = images
        await state.update_data(product_data=product_data)
        
        await callback.message.edit_text(
            f"🗑 已删除最后一张图片。\n\n当前已上传 {len(images)} 张图片。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📸 添加更多图片", callback_data="add_more_product_images")] if len(images) < 5 else [],
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="product_images_done")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
            ])
        )
    else:
        await callback.message.edit_text(
            "❌ 没有可删除的图片。",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ 图片完成", callback_data="product_images_done")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
            ])
        )


@router.callback_query(ProductManagementStates.uploading_product_images, F.data == "product_images_done")
async def product_images_done(callback: CallbackQuery, state: FSMContext):
    """完成商品图片上传"""
    await callback.answer()
    await show_product_confirmation(callback.message, state)


async def show_product_confirmation(message: Message, state: FSMContext):
    """显示商品确认信息"""
    # 显示确认信息
    user_data = await state.get_data()
    product_data = user_data.get("product_data", {})
    
    confirmation_text = "🔍 请确认您的商品信息：\n\n"
    confirmation_text += f"🏷️ 商品名称：{product_data['name']}\n"
    confirmation_text += f"📂 商品分类：{product_data['category_name']}\n"
    
    if product_data.get('description'):
        confirmation_text += f"📄 商品描述：{product_data['description']}\n"
    
    if product_data.get('price') is not None:
        confirmation_text += f"💰 商品价格：¥{product_data['price']}\n"
    
    if product_data.get('tags'):
        confirmation_text += f"🔖 商品标签：{', '.join(product_data['tags'])}\n"
    
    if product_data.get('images'):
        confirmation_text += f"🖼️ 商品图片：已上传 {len(product_data['images'])} 张\n"
    
    confirmation_text += "\n✨ 发布后您的商品将对附近用户可见"
    
    await state.set_state(ProductManagementStates.confirming_product)
    await message.edit_text(confirmation_text, reply_markup=get_confirmation_keyboard())


@router.callback_query(F.data == "confirm_product")
async def confirm_product_creation(callback: CallbackQuery, state: FSMContext):
    """确认创建商品"""
    user_data = await state.get_data()
    product_data = user_data.get("product_data", {})
    
    # 调用API创建商品
    try:
        async with httpx.AsyncClient() as client:
            # 准备商品数据
            api_product_data = {
                "name": product_data['name'],
                "description": product_data.get('description'),
                "price": product_data.get('price'),
                "category_id": product_data['category_id'],
                "tags": product_data.get('tags', []),
                "image_urls": product_data.get('images', []),  # 添加图片URL
                "status": "pending_moderation"  # 初始状态设为待审核
            }
            
            # 获取用户认证信息（从状态中获取）
            auth_data = await state.get_data()
            access_token = auth_data.get("access_token")
            
            if not access_token:
                raise Exception("未找到访问令牌")
            
            # 调用API创建商品
            response = await client.post(
                f"{settings.API_BASE_URL}/api/v1/products/",
                json=api_product_data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 201:
                api_response = response.json()
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ 创建商品时发生错误，请稍后重试或联系客服。\n错误详情: {str(e)}"
            )
        await state.clear()
        await callback.answer()
        return
    
    price_display = f"¥{product_data['price']}" if product_data.get('price') is not None else "面议"
    
    if callback.message:
        await callback.message.edit_text(
            "🎉 恭喜！您的商品已成功发布！\n\n"
            f"🏷️ 商品名称：{product_data['name']}\n"
            f"📂 商品分类：{product_data['category_name']}\n"
            f"💰 商品价格：{price_display}\n\n"
            "✅ 您的商品现在对附近用户可见\n\n"
            "💡 您可以随时编辑或下架商品",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏪 商家管理中心", callback_data="back_to_main")],
                [InlineKeyboardButton(text="📦 管理商品", callback_data="manage_products")]
            ])
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_product_creation")
async def cancel_product_creation(callback: CallbackQuery, state: FSMContext):
    """取消商品创建流程"""
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            "❌ 已取消商品发布流程\n\n"
            "您可以随时重新发布商品！"
        )
    await callback.answer()


@router.callback_query(F.data == "manage_products")
async def manage_products(callback: CallbackQuery, state: FSMContext):
    """管理商品"""
    # 从API获取商家的商品列表
    try:
        async with httpx.AsyncClient() as client:
            # 获取用户认证信息
            auth_data = await state.get_data()
            access_token = auth_data.get("access_token")
            
            if not access_token:
                raise Exception("未找到访问令牌")
            
            # 调用API获取商品列表
            response = await client.get(
                f"{settings.API_BASE_URL}/api/v1/products/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                api_response = response.json()
                products = api_response.get("products", [])
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ 获取商品列表时发生错误，请稍后重试或联系客服。\n错误详情: {str(e)}"
            )
        await callback.answer()
        return
    
    text = "📦 商品管理\n\n"
    for product in products:
        status_emoji = "✅" if product.get("status") == "active" else "❌"
        price = product.get("price")
        price_display = f"¥{price}" if price else "面议"
        text += f"{status_emoji} {product['name']} - {price_display}\n"
    
    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ 添加新商品", callback_data="add_product")],
                [InlineKeyboardButton(text="🔙 返回", callback_data="back_to_main")]
            ])
        )
    await callback.answer()


# 添加用于编辑商品图片的新处理器
@router.callback_query(F.data.startswith("edit_product_images_"))
async def edit_product_images(callback: CallbackQuery, state: FSMContext):
    """编辑商品图片"""
    product_id = int(callback.data.split("_")[-1])
    
    # 保存产品ID到状态
    await state.update_data(editing_product_id=product_id)
    await state.set_state(ProductManagementStates.uploading_product_images)
    
    if callback.message:
        await callback.message.edit_text(
            "🖼️ 请上传新的商品图片\n"
            "• 最多可上传5张图片\n"
            "• 支持 JPG、PNG、WebP 格式\n"
            "• 每张图片不超过10MB\n\n"
            "请发送第一张图片：",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ 完成编辑", callback_data="finish_editing_images")],
                [InlineKeyboardButton(text="❌ 取消", callback_data="cancel_product_creation")]
            ])
        )
    await callback.answer()


@router.callback_query(F.data == "finish_editing_images")
async def finish_editing_images(callback: CallbackQuery, state: FSMContext):
    """完成编辑图片"""
    # 获取更新的图片URL
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    product_data = data.get("product_data", {})
    image_urls = product_data.get("images", [])
    
    # 调用API更新商品图片
    try:
        async with httpx.AsyncClient() as client:
            # 获取用户认证信息
            auth_data = await state.get_data()
            access_token = auth_data.get("access_token")
            
            if not access_token:
                raise Exception("未找到访问令牌")
            
            # 调用API更新商品
            response = await client.put(
                f"{settings.API_BASE_URL}/api/v1/products/{product_id}",
                json={"image_urls": image_urls},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                if callback.message:
                    await callback.message.edit_text(
                        "✅ 商品图片已成功更新！",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="📦 管理商品", callback_data="manage_products")],
                            [InlineKeyboardButton(text="🏪 商家中心", callback_data="back_to_main")]
                        ])
                    )
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
    except Exception as e:
        if callback.message:
            await callback.message.edit_text(
                f"❌ 更新商品图片时发生错误，请稍后重试或联系客服。\n错误详情: {str(e)}"
            )
    
    await state.clear()
    await callback.answer()
