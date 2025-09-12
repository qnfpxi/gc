#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM配置修复脚本

此脚本用于修复NiubiAI中的LLM配置问题，主要解决以下问题：
1. 修复common/llm_utils.py中的LLMConfig类，添加get方法
2. 添加缺失的RetryableError类
3. 重启应用服务
"""

import os
import sys
import time
import subprocess

# 修复后的LLMConfig类代码
FIXED_LLM_UTILS = '''
class LLMConfig:
    def __init__(self, model_name, api_key, provider="openai", api_url=None, max_tokens=2000, temperature=0.7, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.provider = provider
        self.api_url = api_url
        self.base_url = api_url  # 兼容性
        self.max_tokens = max_tokens
        self.temperature = temperature
        # 存储其他参数
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def get(self, key, default=None):
        """获取配置属性，如果不存在则返回默认值。"""
        return getattr(self, key, default)

class RetryableError(Exception):
    """可重试的错误。"""
    pass
'''

# Gemini API密钥配置
GEMINI_API_KEY = "AIzaSyDJC0UxTdU2DjfmXj9S5LbjEWQDi5tuFnI"

def run_command(command):
    """运行shell命令并返回输出"""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None

def fix_llm_config():
    """修复LLM配置问题"""
    print("===== 开始修复LLM配置问题 =====")
    
    # 1. 备份原文件
    run_command("cp /opt/niubiai/common/llm_utils.py /opt/niubiai/common/llm_utils.py.bak")
    print("已备份原始文件到 /opt/niubiai/common/llm_utils.py.bak")
    
    # 2. 写入修复后的代码
    with open("/opt/niubiai/common/llm_utils.py", "w") as f:
        f.write(FIXED_LLM_UTILS.strip())
    print("已更新 /opt/niubiai/common/llm_utils.py 文件")
    
    # 3. 更新Gemini API密钥
    run_command(f"sed -i 's/GEMINI_API_KEY=your-gemini-key/GEMINI_API_KEY={GEMINI_API_KEY}/g' /opt/niubiai/.env")
    run_command(f"sed -i 's/GOOGLE_API_KEY=your-google-api-key/GOOGLE_API_KEY={GEMINI_API_KEY}/g' /opt/niubiai/.env")
    print("已更新Gemini API密钥配置")
    
    # 4. 重启应用
    run_command("pkill -f 'python3 main.py' || true")
    run_command("cd /opt/niubiai && (nohup python3 main.py > logs/startup.log 2>&1 &)")
    print("已重启应用")
    
    # 5. 等待应用启动
    print("等待应用启动...")
    time.sleep(5)
    
    # 6. 检查应用状态
    ps_output = run_command("ps aux | grep 'python3 main.py' | grep -v grep")
    if ps_output and ps_output.strip():
        print("✅ 应用已成功启动")
    else:
        print("❌ 应用启动失败，请检查日志")
        run_command("tail -n 20 /opt/niubiai/logs/startup.log")
    
    print("===== LLM配置修复完成 =====")

if __name__ == "__main__":
    fix_llm_config()