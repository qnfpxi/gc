#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复NiubiAI Bot的网络错误问题

这个脚本会修改app/application.py文件，增加网络超时时间和重试机制，
以解决httpx.ReadError和NetworkError问题。
"""

import os
import re
import sys
import shutil

# 服务器上的项目路径
PROJECT_PATH = "/opt/niubiai"

# 备份文件路径
BACKUP_PATH = os.path.join(PROJECT_PATH, "app/application.py.bak")

# 目标文件路径
TARGET_PATH = os.path.join(PROJECT_PATH, "app/application.py")

# 检查备份文件是否存在
if not os.path.exists(BACKUP_PATH):
    print(f"错误: 备份文件 {BACKUP_PATH} 不存在，请先创建备份")
    sys.exit(1)

# 读取原始文件内容
with open(TARGET_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 修改1: 增加超时时间
timeout_pattern = r'"timeout": httpx\.Timeout\(\s*connect=(\d+\.\d+),\s*read=(\d+\.\d+),\s*write=(\d+\.\d+),\s*pool=(\d+\.\d+)\s*\)'
timeout_replacement = '"timeout": httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=60.0)'

content = re.sub(timeout_pattern, timeout_replacement, content)

# 修改2: 增加HTTPXRequest的超时时间
request_pattern = r'request = HTTPXRequest\(\s*connection_pool_size=\d+,\s*read_timeout=(\d+\.\d+),\s*write_timeout=(\d+\.\d+)'
request_replacement = 'request = HTTPXRequest(\n                connection_pool_size=100,\n                read_timeout=60.0,\n                write_timeout=60.0'

content = re.sub(request_pattern, request_replacement, content)

# 修改3: 增加轮询超时时间
polling_pattern = r'await self\.app\.updater\.start_polling\(\s*allowed_updates=\["message", "callback_query"\],\s*drop_pending_updates=True,\s*poll_interval=\d+\.\d+,\s*timeout=(\d+)\s*\)'
polling_replacement = 'await self.app.updater.start_polling(\n                allowed_updates=["message", "callback_query"],\n                drop_pending_updates=True,\n                poll_interval=1.0,\n                timeout=30\n            )'

content = re.sub(polling_pattern, polling_replacement, content)

# 修改4: 添加重试机制的导入
import_pattern = r'import asyncio\nimport ssl\nimport time'
import_replacement = 'import asyncio\nimport ssl\nimport time\nimport random\nfrom telegram.error import RetryAfter, TimedOut, NetworkError'

content = re.sub(import_pattern, import_replacement, content)

# 修改5: 在start方法中添加重试机制
start_pattern = r'async def start\(self\):\n        """启动Bot\."""\n        startup_tasks = \[\]\n        try:'
start_replacement = 'async def start(self):\n        """启动Bot."""
        startup_tasks = []\n        retry_count = 0\n        max_retries = 5\n        try:'

content = re.sub(start_pattern, start_replacement, content)

# 修改6: 在启动轮询部分添加重试逻辑
start_polling_pattern = r'# 启动轮询\n            await self\.app\.updater\.start_polling\('
start_polling_replacement = '# 启动轮询，添加重试机制\n            retry_success = False\n            while not retry_success and retry_count < max_retries:\n                try:\n                    await self.app.updater.start_polling('

after_polling_pattern = r'\)\n\n            # 保持运行'
after_polling_replacement = ')\n                    retry_success = True\n                    logger.info("轮询启动成功")\n                except (NetworkError, TimedOut, RetryAfter) as e:\n                    retry_count += 1\n                    wait_time = 2 ** retry_count + random.uniform(0, 1)  # 指数退避策略\n                    logger.warning(f"轮询启动失败，正在重试 ({retry_count}/{max_retries})，等待 {wait_time:.2f} 秒: {e}")\n                    await asyncio.sleep(wait_time)\n                except Exception as e:\n                    logger.error(f"轮询启动失败，无法恢复的错误: {e}", exc_info=True)\n                    raise\n            \n            if not retry_success:\n                raise RuntimeError(f"轮询启动失败，已重试 {max_retries} 次")\n\n            # 保持运行'

content = re.sub(start_polling_pattern, start_polling_replacement, content)
content = re.sub(after_polling_pattern, after_polling_replacement, content)

# 写入修改后的内容
with open(TARGET_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 成功修改 {TARGET_PATH}")
print("修改内容:")
print("1. 增加网络超时时间从30秒到60秒")
print("2. 增加轮询超时时间从10秒到30秒")
print("3. 添加启动轮询的重试机制，最多重试5次，使用指数退避策略")
print("\n请重启Bot以应用更改:")
print("cd /opt/niubiai && python3 main.py")