"""
商品审核 Celery 任务

将商品审核逻辑重构为可重试的、健壮的 Celery task
"""

import asyncio
import json
from celery import current_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
import time

from app.core.celery_app import celery_app
from app.config import settings
from app.services.moderation_service import ModerationService
from app.services.ai.moderation import get_moderation_decision

# 配置日志
logger = logging.getLogger(__name__)

# 数据库连接
db_engine = create_engine(settings.DATABASE_URL)
DbSession = sessionmaker(bind=db_engine)

# AI 审核服务
moderation_service = ModerationService()

# 内部API配置
INTERNAL_API_KEY = settings.SECRET_KEY
API_BASE_URL = settings.API_BASE_URL + "/api/v1"


@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器"""
    session = DbSession()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_product_info(product_id: str):
    """从数据库获取商品信息"""
    try:
        with get_db_session() as session:
            # 查询商品信息
            query = text("""
                SELECT name, description, merchant_id
                FROM products
                WHERE id = :product_id
            """)
            result = session.execute(query, {"product_id": product_id}).fetchone()
            
            if result:
                return {
                    "name": result.name,
                    "description": result.description,
                    "merchant_id": result.merchant_id
                }
            return None
    except Exception as e:
        logger.error(f"Failed to get product info: {e}")
        return None


def get_product_with_merchant(product_id: str):
    """从数据库获取商品和商家信息"""
    try:
        with get_db_session() as session:
            # 查询商品和商家信息
            query = text("""
                SELECT p.name as product_name, p.merchant_id, m.telegram_chat_id
                FROM products p
                JOIN merchants m ON p.merchant_id = m.id
                WHERE p.id = :product_id
            """)
            result = session.execute(query, {"product_id": product_id}).fetchone()
            
            if result:
                return {
                    "product_name": result.product_name,
                    "merchant_id": result.merchant_id,
                    "merchant_chat_id": result.telegram_chat_id
                }
            return None
    except Exception as e:
        logger.error(f"Failed to get product with merchant: {e}")
        return None


def update_product_status(product_id: str, status: str):
    """更新商品状态"""
    try:
        import httpx
        
        url = f"{API_BASE_URL}/products/{product_id}/status"
        headers = {
            "X-Internal-Key": INTERNAL_API_KEY,
            "Content-Type": "application/json"
        }
        data = {"status": status}
        
        # 使用同步HTTP客户端
        with httpx.Client() as client:
            response = client.patch(url, json=data, headers=headers)
            response.raise_for_status()
        
        logger.info(f"Updated product {product_id} status to {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update product {product_id} status: {e}")
        raise


def update_product_status_with_notes(product_id: str, status: str, notes: str):
    """更新商品状态和审核备注"""
    try:
        import httpx
        
        url = f"{API_BASE_URL}/products/{product_id}/status"
        headers = {
            "X-Internal-Key": INTERNAL_API_KEY,
            "Content-Type": "application/json"
        }
        data = {"status": status, "moderation_notes": notes}
        
        # 使用同步HTTP客户端
        with httpx.Client() as client:
            response = client.patch(url, json=data, headers=headers)
            response.raise_for_status()
        
        logger.info(f"Updated product {product_id} status to {status} with notes: {notes}")
        return True
    except Exception as e:
        logger.error(f"Failed to update product {product_id} status with notes: {e}")
        raise


def send_rejection_notification(chat_id: str, product_name: str, reason: str):
    """发送拒绝通知给商家（包含具体原因）"""
    import asyncio
    bot = None
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # 创建Bot实例
        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # 构造拒绝消息（包含具体原因）
        message = f"""
❌ <b>商品审核未通过</b>

您的商品 "<i>{product_name}</i>" 未能通过审核。

<b>原因：</b>
{reason}

请修改后重新提交。如有疑问，请联系客服。

感谢您的理解与配合！
        """
        
        # 发送消息
        asyncio.run(bot.send_message(chat_id=chat_id, text=message))
        
        logger.info(f"Sent rejection notification to merchant {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {e}")
        raise
    finally:
        # 确保即使出错也关闭bot会话
        if bot is not None:
            try:
                asyncio.run(bot.session.close())
            except:
                pass


def publish_moderation_notification(product_id: str, merchant_id: str, status: str, notes: str):
    """发布审核通知到Redis"""
    try:
        import redis
        
        # 连接到Redis（使用Celery的Broker URL，但不同的数据库）
        redis_client = redis.from_url(str(settings.CELERY_BROKER_URL), db=0)
        
        # 构造通知消息
        notification = {
            "type": "product_moderation_update",
            "product_id": int(product_id),
            "merchant_id": merchant_id,
            "status": status,
            "moderation_notes": notes,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        # 发布到notifications频道
        redis_client.publish("notifications", json.dumps(notification))
        logger.info(f"Published moderation notification for product {product_id} to user {merchant_id}")
        
        # 关闭连接
        redis_client.close()
        
    except Exception as e:
        logger.error(f"Failed to publish moderation notification: {e}")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def moderate_product(self, product_id: str):
    """
    商品审核 Celery 任务
    
    Args:
        product_id (str): 商品ID
        
    Returns:
        dict: 审核结果
    """
    logger.info(f"Processing moderation for product {product_id}")
    
    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 4, 'status': '获取商品信息'})
        
        # 从数据库获取完整的商品信息
        product_info = get_product_info(product_id)
        if not product_info:
            logger.warning(f"Product {product_id} not found")
            return {"status": "failed", "reason": "Product not found"}
            
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 4, 'status': 'AI审核中'})
        
        # 使用AI审核服务审核商品内容
        moderation_result = get_moderation_decision(
            product_info["name"], 
            product_info["description"] or ""
        )
        
        # 根据AI结果决定状态
        new_status = "active" if moderation_result.decision == "approved" else "rejected"
        reason = moderation_result.reason
        
        logger.info(f"Moderation result for product {product_id}: {new_status.upper()}. Reason: {reason}")
        
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'current': 3, 'total': 4, 'status': '更新商品状态'})
        
        # 更新商品状态和审核备注
        update_product_status_with_notes(product_id, new_status, reason)
        
        # 发布审核通知
        publish_moderation_notification(product_id, str(product_info["merchant_id"]), new_status, reason)
        
        # 如果被拒绝，通知商家（通过Bot）
        if new_status == "rejected":
            self.update_state(state='PROGRESS', meta={'current': 4, 'total': 4, 'status': '发送通知'})
            product_with_merchant = get_product_with_merchant(product_id)
            if product_with_merchant and product_with_merchant.get("merchant_chat_id"):
                send_rejection_notification(
                    product_with_merchant["merchant_chat_id"],
                    product_with_merchant["product_name"],
                    reason
                )
        
        return {
            "status": "success",
            "product_id": product_id,
            "decision": moderation_result.decision,
            "reason": reason
        }
        
    except Exception as exc:
        logger.error(f"Error during moderation process for product {product_id}: {exc}")
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for product {product_id}. Retry {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc)
        else:
            logger.error(f"Max retries exceeded for product {product_id}")
            # 即使重试失败，也要更新商品状态为审核失败
            try:
                update_product_status(product_id, "moderation_failed")
                # 也要发布通知
                product_info = get_product_info(product_id)
                if product_info:
                    publish_moderation_notification(
                        product_id, 
                        str(product_info["merchant_id"]), 
                        "moderation_failed", 
                        "审核过程失败"
                    )
            except Exception as update_exc:
                logger.error(f"Failed to update product status after max retries: {update_exc}")
            
            return {
                "status": "failed",
                "product_id": product_id,
                "error": str(exc)
            }