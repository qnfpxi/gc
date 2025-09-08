"""
WebSocket连接管理器

管理所有活跃的WebSocket连接，支持同一用户的多个连接
"""

import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储活跃连接的字典，key为user_id，value为WebSocket连接列表
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """
        添加用户连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 接受WebSocket连接
            await websocket.accept()
            
            # 如果用户ID不在字典中，初始化一个空列表
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            # 将连接添加到用户连接列表中
            self.active_connections[user_id].append(websocket)
            
            logger.info(f"WebSocket connection established for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for user {user_id}: {e}")
            return False

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        移除用户连接
        
        Args:
            websocket: WebSocket连接对象
            user_id: 用户ID
        """
        try:
            # 从用户连接列表中移除连接
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                    
                    # 如果用户没有其他连接，删除用户键
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
            
            logger.info(f"WebSocket connection closed for user {user_id}")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket for user {user_id}: {e}")

    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """
        向指定用户发送消息
        
        Args:
            message: 要发送的消息（字典格式）
            user_id: 用户ID
        """
        try:
            # 检查用户是否有活跃连接
            if user_id in self.active_connections:
                # 向用户的所有连接发送消息
                for connection in self.active_connections[user_id][:]:  # 使用切片创建副本以防在迭代时修改
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send message to user {user_id}: {e}")
                        # 如果发送失败，移除连接
                        self.disconnect(connection, user_id)
            else:
                logger.debug(f"No active connections for user {user_id}, message not sent")
        except Exception as e:
            logger.error(f"Error sending personal message to user {user_id}: {e}")

    async def broadcast(self, message: dict) -> None:
        """
        广播消息给所有连接的用户
        
        Args:
            message: 要广播的消息（字典格式）
        """
        try:
            # 创建所有连接的副本列表，以防在发送过程中连接发生变化
            all_connections = []
            for connections in self.active_connections.values():
                all_connections.extend(connections)
            
            # 向所有连接发送消息
            for connection in all_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast message: {e}")
                    # 如果发送失败，移除连接
                    # 注意：这里需要找到连接对应的用户ID才能正确移除
                    # 为简化实现，我们只记录错误
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")

    def get_user_connection_count(self, user_id: str) -> int:
        """
        获取指定用户的连接数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 连接数
        """
        return len(self.active_connections.get(user_id, []))

    def get_total_connection_count(self) -> int:
        """
        获取总连接数
        
        Returns:
            int: 总连接数
        """
        return sum(len(connections) for connections in self.active_connections.values())