"""
WebSocket通知端点

提供实时通知功能的WebSocket端点
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# 创建全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket端点，用于接收客户端连接
    
    Args:
        websocket: WebSocket连接对象
        user_id: 用户ID（从路径参数获取）
    """
    try:
        # 建立连接
        connected = await manager.connect(websocket, user_id)
        if not connected:
            logger.error(f"Failed to establish WebSocket connection for user {user_id}")
            return
            
        # 发送连接成功的消息
        await websocket.send_json({
            "type": "connection_ack",
            "message": "Connected successfully",
            "user_id": user_id
        })
        
        # 保持连接并处理消息
        while True:
            # 接收客户端消息（可选，用于心跳或其他功能）
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
            
            # 可以在这里处理客户端发送的消息
            # 例如，实现心跳机制
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)