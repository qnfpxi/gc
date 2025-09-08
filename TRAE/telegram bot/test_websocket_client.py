#!/usr/bin/env python3
"""
WebSocket测试客户端

用于测试WebSocket通知功能
"""

import asyncio
import websockets
import json
import sys


async def test_websocket_notifications(user_id: str, host: str = "localhost", port: int = 8000):
    """
    测试WebSocket通知功能
    
    Args:
        user_id: 用户ID
        host: 服务器主机名
        port: 服务器端口
    """
    uri = f"ws://{host}:{port}/api/v1/notifications/ws/{user_id}"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket server as user {user_id}")
            print("Waiting for notifications... (Press Ctrl+C to exit)")
            
            # 接收并打印所有消息
            while True:
                try:
                    message = await websocket.recv()
                    try:
                        data = json.loads(message)
                        print(f"\n--- Notification Received ---")
                        print(f"Type: {data.get('type', 'unknown')}")
                        print(f"Product ID: {data.get('product_id', 'N/A')}")
                        print(f"Status: {data.get('status', 'N/A')}")
                        print(f"Notes: {data.get('moderation_notes', 'N/A')}")
                        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
                        print("-----------------------------\n")
                    except json.JSONDecodeError:
                        print(f"Received non-JSON message: {message}")
                        
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Error connecting to WebSocket server: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_websocket_client.py <user_id> [host] [port]")
        print("Example: python test_websocket_client.py 123")
        sys.exit(1)
    
    user_id = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
    
    print(f"Starting WebSocket client for user {user_id}")
    asyncio.run(test_websocket_notifications(user_id, host, port))