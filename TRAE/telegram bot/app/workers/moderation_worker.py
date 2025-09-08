#!/usr/bin/env python3
"""
商品审核Worker服务

独立的后台服务，持续消费审核队列，执行审核，并更新商品状态
"""

import asyncio
import logging
import random
from typing import Dict, Any
import aioredis
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time

from app.config import settings
from app.services.moderation_service import ModerationService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus 指标定义
# Counter: 只增不减的计数器
PRODUCTS_MODERATED = Counter('products_moderated_total', 'Total number of products moderated', ['decision'])
OPENAI_API_ERRORS = Counter('openai_api_errors_total', 'Total number of OpenAI API errors')
NOTIFICATION_SENT = Counter('moderation_notifications_sent_total', 'Total number of moderation notifications sent', ['status'])

# Histogram: 统计数据分布，如请求耗时
MODERATION_DURATION = Histogram('moderation_duration_seconds', 'Time spent on a single product moderation')
REDIS_PROCESSING_DURATION = Histogram('redis_processing_duration_seconds', 'Time spent processing Redis messages')
API_CALL_DURATION = Histogram('api_call_duration_seconds', 'Time spent on API calls')

# Gauge: 可增可减的指标
REDIS_QUEUE_SIZE = Gauge('redis_moderation_queue_size', 'Current size of the Redis moderation queue')

# Redis Stream配置
MODERATION_STREAM_KEY = "product_moderation_queue"
CONSUMER_GROUP = "moderation_workers"
CONSUMER_NAME = "worker_1"  # 在生产环境中应该使用唯一名称

# 内部API配置
INTERNAL_API_KEY = settings.SECRET_KEY  # 使用应用的SECRET_KEY作为内部API密钥
API_BASE_URL = settings.API_BASE_URL + "/api/v1"  # 从配置中获取API基础URL

class ModerationWorker:
    """商品审核Worker"""
    
    def __init__(self):
        self.redis = None
        self.http_client = None
        self.db_engine = None
        self.db_session = None
        self.moderation_service = ModerationService()
        self.metrics_port = 8001  # Prometheus指标暴露端口
        
    async def initialize(self):
        """初始化Worker"""
        # 初始化Redis连接
        self.redis = await aioredis.from_url(
            str(settings.REDIS_URL),
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        
        # 创建HTTP客户端
        self.http_client = httpx.AsyncClient()
        
        # 创建数据库连接
        self.db_engine = create_engine(settings.DATABASE_URL)
        self.db_session = sessionmaker(bind=self.db_engine)
        
        # 创建消费者组
        try:
            await self.redis.xgroup_create(
                MODERATION_STREAM_KEY, 
                CONSUMER_GROUP, 
                id="0", 
                mkstream=True
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(f"Consumer group {CONSUMER_GROUP} already exists")
    
    async def run(self):
        """运行Worker"""
        await self.initialize()
        logger.info("Moderation worker started")
        
        # 启动Prometheus指标服务器
        start_http_server(self.metrics_port)
        logger.info(f"Prometheus metrics server started on port {self.metrics_port}")
        
        while True:
            try:
                # 更新Redis队列大小指标
                queue_length = await self.redis.xlen(MODERATION_STREAM_KEY)
                REDIS_QUEUE_SIZE.set(queue_length)
                
                # 从Stream中读取待处理任务
                start_time = time.time()
                messages = await self.redis.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {MODERATION_STREAM_KEY: ">"},
                    count=1,
                    block=5000  # 5秒超时
                )
                redis_duration = time.time() - start_time
                REDIS_PROCESSING_DURATION.observe(redis_duration)
                
                if messages:
                    for stream_key, message_list in messages:
                        for message_id, message_data in message_list:
                            try:
                                await self.process_moderation_task(message_data)
                                # 确认消息处理完成
                                await self.redis.xack(
                                    MODERATION_STREAM_KEY,
                                    CONSUMER_GROUP,
                                    message_id
                                )
                                logger.info(f"Processed message {message_id}")
                            except Exception as e:
                                logger.error(f"Failed to process message {message_id}: {e}")
                                # 可以选择重新入队或移到死信队列
                else:
                    logger.debug("No messages in queue, waiting...")
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)  # 避免快速重试
    
    async def process_moderation_task(self, message_data: Dict[str, Any]):
        """处理审核任务"""
        product_id = message_data.get("product_id")
        if not product_id:
            logger.warning("Invalid message data: missing product_id")
            return
            
        logger.info(f"Processing moderation for product {product_id}")
        
        start_time = time.time()
        try:
            # 从数据库获取完整的商品信息
            product_info = self.get_product_info(product_id)
            if not product_info:
                logger.warning(f"Product {product_id} not found")
                return
                
            # 使用AI审核服务审核商品内容
            moderation_result = self.moderation_service.moderate_product_content(
                product_info["name"], 
                product_info["description"] or ""
            )
            
            # 根据AI结果决定状态
            new_status = "active" if moderation_result.decision == "approved" else "rejected"
            reason = moderation_result.reason
            
            logger.info(f"Moderation result for product {product_id}: {new_status.upper()}. Reason: {reason}")
            
            # 更新商品状态
            await self.update_product_status(product_id, new_status)
            
            # 更新Prometheus指标
            PRODUCTS_MODERATED.labels(decision=moderation_result.decision).inc()
            
            # 如果被拒绝，通知商家（通过Bot）
            if new_status == "rejected":
                await self.notify_merchant_of_rejection(product_id, reason)
                NOTIFICATION_SENT.labels(status="sent").inc()
            else:
                NOTIFICATION_SENT.labels(status="skipped").inc()
                
        except Exception as e:
            logger.error(f"Error during moderation process for product {product_id}: {e}")
            OPENAI_API_ERRORS.inc()
            # 即使出错也要记录处理时间
            duration = time.time() - start_time
            MODERATION_DURATION.observe(duration)
            raise
        finally:
            # 记录处理时间
            duration = time.time() - start_time
            MODERATION_DURATION.observe(duration)
    
    def get_product_info(self, product_id: str) -> dict:
        """从数据库获取商品信息"""
        try:
            with self.db_session() as session:
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
    
    async def update_product_status(self, product_id: str, status: str):
        """更新商品状态"""
        start_time = time.time()
        try:
            url = f"{API_BASE_URL}/products/{product_id}/status"
            headers = {
                "X-Internal-Key": INTERNAL_API_KEY,
                "Content-Type": "application/json"
            }
            data = {"status": status}
            
            response = await self.http_client.patch(url, json=data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Updated product {product_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update product {product_id} status: {e}")
            raise
        finally:
            duration = time.time() - start_time
            API_CALL_DURATION.observe(duration)
    
    async def notify_merchant_of_rejection(self, product_id: str, reason: str):
        """通知商家商品被拒绝（通过Bot）"""
        try:
            # 从数据库获取商品和商家信息
            product_info = self.get_product_with_merchant(product_id)
            if not product_info:
                logger.warning(f"Product {product_id} not found")
                return
                
            merchant_chat_id = product_info.get("merchant_chat_id")
            product_name = product_info.get("product_name")
            
            if not merchant_chat_id:
                logger.warning(f"Merchant chat ID not found for product {product_id}")
                return
                
            # 发送拒绝通知消息（包含具体原因）
            await self.send_rejection_notification(merchant_chat_id, product_name, reason)
            logger.info(f"Sent rejection notification to merchant for product {product_id}")
        except Exception as e:
            logger.error(f"Failed to notify merchant about rejection of product {product_id}: {e}")
            NOTIFICATION_SENT.labels(status="failed").inc()
    
    def get_product_with_merchant(self, product_id: str) -> dict:
        """从数据库获取商品和商家信息"""
        try:
            with self.db_session() as session:
                # 查询商品和商家信息
                query = text("""
                    SELECT p.name as product_name, m.telegram_chat_id
                    FROM products p
                    JOIN merchants m ON p.merchant_id = m.id
                    WHERE p.id = :product_id
                """)
                result = session.execute(query, {"product_id": product_id}).fetchone()
                
                if result:
                    return {
                        "product_name": result.product_name,
                        "merchant_chat_id": result.telegram_chat_id
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get product with merchant: {e}")
            return None
    
    async def send_rejection_notification(self, chat_id: str, product_name: str, reason: str):
        """发送拒绝通知给商家（包含具体原因）"""
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
            await bot.send_message(chat_id=chat_id, text=message)
            await bot.session.close()
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {e}")
            # 确保即使出错也关闭bot会话
            try:
                await bot.session.close()
            except:
                pass
            raise
    
    async def shutdown(self):
        """关闭Worker"""
        if self.http_client:
            await self.http_client.aclose()
        if self.redis:
            await self.redis.close()
        logger.info("Moderation worker shutdown complete")


async def main():
    """主函数"""
    worker = ModerationWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())