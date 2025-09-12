#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram机器人响应测试脚本
"""

import requests
import json
import time
import sys

# 机器人配置
BOT_TOKEN = "8429084641:AAGoLX_FPmIztPN7MPVzEdBxmO-VdYMYkTU"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 测试用的chat_id (需要替换为实际的chat_id)
TEST_CHAT_ID = "123456789"  # 请替换为您的实际chat_id

def test_bot_info():
    """测试机器人基本信息"""
    print("=== 测试机器人基本信息 ===")
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        data = response.json()
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ 机器人信息获取成功:")
            print(f"   - 名称: {bot_info.get('first_name')}")
            print(f"   - 用户名: @{bot_info.get('username')}")
            print(f"   - ID: {bot_info.get('id')}")
            return True
        else:
            print(f"❌ 获取机器人信息失败: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def test_webhook_status():
    """检查webhook状态"""
    print("\n=== 检查Webhook状态 ===")
    try:
        response = requests.get(f"{BASE_URL}/getWebhookInfo", timeout=10)
        data = response.json()
        if data.get('ok'):
            webhook_info = data['result']
            url = webhook_info.get('url', '')
            pending_count = webhook_info.get('pending_update_count', 0)
            
            if url:
                print(f"⚠️  Webhook已设置: {url}")
                print(f"   - 待处理更新数: {pending_count}")
                print("   - 建议: 如果使用polling模式，应删除webhook")
            else:
                print("✅ 未设置Webhook (适合polling模式)")
                print(f"   - 待处理更新数: {pending_count}")
            return True
        else:
            print(f"❌ 获取Webhook信息失败: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def get_updates():
    """获取最新消息更新"""
    print("\n=== 获取最新消息更新 ===")
    try:
        response = requests.get(f"{BASE_URL}/getUpdates?limit=5", timeout=10)
        data = response.json()
        if data.get('ok'):
            updates = data['result']
            print(f"✅ 成功获取 {len(updates)} 条更新")
            
            if updates:
                print("最近的消息:")
                for update in updates[-3:]:  # 显示最近3条
                    update_id = update.get('update_id')
                    message = update.get('message', {})
                    chat_id = message.get('chat', {}).get('id')
                    text = message.get('text', '无文本内容')
                    date = message.get('date', 0)
                    
                    print(f"   - 更新ID: {update_id}")
                    print(f"     Chat ID: {chat_id}")
                    print(f"     内容: {text[:50]}{'...' if len(text) > 50 else ''}")
                    print(f"     时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date))}")
                    print()
                    
                    # 如果找到了有效的chat_id，更新全局变量
                    if chat_id:
                        global TEST_CHAT_ID
                        TEST_CHAT_ID = str(chat_id)
                        print(f"📝 已更新测试Chat ID为: {TEST_CHAT_ID}")
            else:
                print("   - 暂无消息更新")
                print("   - 建议: 向机器人发送一条测试消息")
            return True
        else:
            print(f"❌ 获取更新失败: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def send_test_message():
    """发送测试消息"""
    print("\n=== 发送测试消息 ===")
    
    if TEST_CHAT_ID == "123456789":
        print("⚠️  未找到有效的Chat ID")
        print("   请先向机器人发送一条消息，然后重新运行此脚本")
        return False
    
    test_message = f"🤖 机器人测试消息\n时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n状态: 正常运行"
    
    try:
        payload = {
            'chat_id': TEST_CHAT_ID,
            'text': test_message
        }
        
        response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        data = response.json()
        
        if data.get('ok'):
            message_id = data['result'].get('message_id')
            print(f"✅ 测试消息发送成功")
            print(f"   - 消息ID: {message_id}")
            print(f"   - Chat ID: {TEST_CHAT_ID}")
            return True
        else:
            error_desc = data.get('description', '未知错误')
            print(f"❌ 发送消息失败: {error_desc}")
            
            if 'chat not found' in error_desc.lower():
                print("   - 可能原因: Chat ID无效或机器人未与用户建立对话")
                print("   - 解决方案: 请先在Telegram中向机器人发送 /start 命令")
            
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Telegram机器人响应测试开始")
    print("=" * 50)
    
    # 测试步骤
    tests = [
        ("机器人信息", test_bot_info),
        ("Webhook状态", test_webhook_status),
        ("消息更新", get_updates),
        ("发送测试消息", send_test_message)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 正在测试: {test_name}")
        result = test_func()
        results.append((test_name, result))
        
        if not result:
            print(f"⚠️  {test_name} 测试失败，继续下一项测试...")
    
    # 总结报告
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   - {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(tests)} 项测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！机器人运行正常")
    elif passed >= 2:
        print("⚠️  部分测试通过，机器人基本功能正常")
        print("   建议检查失败的测试项目")
    else:
        print("❌ 多项测试失败，机器人可能存在问题")
        print("   建议检查服务器日志和网络连接")
    
    print("\n💡 使用提示:")
    print("   1. 如果Chat ID测试失败，请先向机器人发送 /start")
    print("   2. 如果Webhook已设置，建议删除以使用polling模式")
    print("   3. 检查服务器防火墙和网络连接")
    print("   4. 查看服务器日志: tail -f /opt/niubiai/bot.log")

if __name__ == "__main__":
    main()