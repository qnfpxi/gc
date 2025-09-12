#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_IP="103.115.64.72"
SERVER_USER="root"
SERVER_PASS="pnooZZMV7257"
APP_DIR="/opt/niubiai"

# 日志文件
LOG_FILE="network_fix_$(date +%Y%m%d_%H%M%S).log"

# 检查sshpass是否安装
check_sshpass() {
    if ! command -v sshpass &> /dev/null; then
        echo -e "${RED}错误: sshpass 未安装!${NC}"
        echo -e "${YELLOW}请先运行 setup_sshpass.sh 脚本安装 sshpass${NC}"
        exit 1
    fi
}

# 执行SSH命令的函数
ssh_command() {
    local command=$1
    echo -e "${BLUE}执行命令: $command${NC}" | tee -a "$LOG_FILE"
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command" 2>&1 | tee -a "$LOG_FILE"
    return ${PIPESTATUS[0]}
}

# 上传文件的函数
scp_upload() {
    local src=$1
    local dest=$2
    echo -e "${BLUE}上传文件: $src 到 $dest${NC}" | tee -a "$LOG_FILE"
    sshpass -p "$SERVER_PASS" scp -o StrictHostKeyChecking=no "$src" "$SERVER_USER@$SERVER_IP:$dest" 2>&1 | tee -a "$LOG_FILE"
    return ${PIPESTATUS[0]}
}

echo -e "${GREEN}===== NiubiAI Bot 网络错误修复脚本 =====${NC}" | tee -a "$LOG_FILE"
echo -e "${BLUE}开始时间: $(date)${NC}" | tee -a "$LOG_FILE"

# 检查sshpass
check_sshpass

# 创建网络修复脚本
cat > fix_network.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复NiubiAI Bot的网络连接问题
主要针对httpx.ReadError错误
"""

import os
import sys
import subprocess
import time
import json

def check_python_version():
    """检查Python版本"""
    print(f"当前Python版本: {sys.version}")
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
        print("警告: 推荐使用Python 3.8或更高版本")

def check_network_connectivity():
    """检查网络连接"""
    print("\n检查网络连接...")
    targets = [
        "api.telegram.org",
        "www.google.com",
        "www.baidu.com"
    ]
    
    for target in targets:
        try:
            result = subprocess.run(["ping", "-c", "3", target], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  timeout=10)
            if result.returncode == 0:
                print(f"✅ {target} 连接正常")
            else:
                print(f"❌ {target} 连接失败")
                print(result.stderr)
        except subprocess.TimeoutExpired:
            print(f"❌ {target} 连接超时")
        except Exception as e:
            print(f"❌ {target} 检查出错: {str(e)}")

def check_proxy_settings():
    """检查代理设置"""
    print("\n检查代理设置...")
    proxy_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
    
    for var in proxy_vars:
        value = os.environ.get(var, "未设置")
        print(f"{var}: {value}")

def update_httpx_package():
    """更新httpx包"""
    print("\n更新httpx包...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "httpx"], 
                      check=True,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      text=True)
        print("✅ httpx包更新成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ httpx包更新失败: {e.stderr}")

def update_python_telegram_bot():
    """更新python-telegram-bot包"""
    print("\n更新python-telegram-bot包...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "python-telegram-bot"], 
                      check=True,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      text=True)
        print("✅ python-telegram-bot包更新成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ python-telegram-bot包更新失败: {e.stderr}")

def modify_request_timeout():
    """修改请求超时设置"""
    print("\n修改请求超时设置...")
    
    # 检查services目录下的文件
    services_dir = "services"
    if not os.path.exists(services_dir):
        print(f"❌ 找不到{services_dir}目录")
        return
    
    # 查找可能包含请求超时设置的文件
    target_files = []
    for root, _, files in os.walk(services_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "httpx" in content or "request" in content or "timeout" in content:
                        target_files.append(file_path)
    
    if not target_files:
        print("❌ 找不到包含请求超时设置的文件")
        return
    
    print(f"找到以下可能包含请求超时设置的文件:")
    for file in target_files:
        print(f"  - {file}")
    
    # 修改文件中的超时设置
    modified = False
    for file_path in target_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 查找并修改timeout参数
        if "timeout=" in content:
            # 增加超时时间
            new_content = content.replace("timeout=5", "timeout=30")
            new_content = new_content.replace("timeout=10", "timeout=60")
            new_content = new_content.replace("timeout=15", "timeout=90")
            
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"✅ 已修改 {file_path} 中的超时设置")
                modified = True
    
    if not modified:
        print("⚠️ 未找到需要修改的超时设置")

def add_retry_mechanism():
    """添加重试机制"""
    print("\n添加重试机制...")
    
    # 检查services目录下的文件
    services_dir = "services"
    if not os.path.exists(services_dir):
        print(f"❌ 找不到{services_dir}目录")
        return
    
    # 查找可能需要添加重试机制的文件
    target_files = []
    for root, _, files in os.walk(services_dir):
        for file in files:
            if file.endswith(".py") and "service" in file.lower():
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "httpx" in content or "request" in content:
                        target_files.append(file_path)
    
    if not target_files:
        print("❌ 找不到需要添加重试机制的文件")
        return
    
    print(f"找到以下可能需要添加重试机制的文件:")
    for file in target_files:
        print(f"  - {file}")
    
    # 创建重试装饰器文件
    retry_decorator_path = os.path.join("common", "retry.py")
    os.makedirs(os.path.dirname(retry_decorator_path), exist_ok=True)
    
    with open(retry_decorator_path, "w", encoding="utf-8") as f:
        f.write("""
# -*- coding: utf-8 -*-
"""
重试装饰器
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, Type, Union, List, Tuple

logger = logging.getLogger(__name__)

def retry(
    max_tries: int = 3,
    delay: float = 1,
    backoff: float = 2,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
):
    """
    重试装饰器
    
    Args:
        max_tries: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的增长因子
        exceptions: 需要捕获的异常类型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay
            last_exception = None
            
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    mtries -= 1
                    if mtries == 0:
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 执行失败 ({str(e)}), "
                        f"将在 {mdelay} 秒后重试. 剩余尝试次数: {mtries}"
                    )
                    
                    time.sleep(mdelay)
                    mdelay *= backoff
            
            # 不应该到达这里，但为了类型检查
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
""")
    
    print(f"✅ 已创建重试装饰器文件: {retry_decorator_path}")
    
    # 修改目标文件，添加重试机制
    modified = False
    for file_path in target_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经导入了retry装饰器
        if "from common.retry import retry" not in content and "import retry" not in content:
            # 添加导入语句
            import_line = "from common.retry import retry\n"
            
            # 查找导入块的结束位置
            import_end = 0
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_end = i + 1
            
            # 插入导入语句
            lines.insert(import_end, import_line)
            
            # 查找可能需要添加装饰器的函数
            modified_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if line.strip().startswith("def ") and ("request" in line or "http" in line or "api" in line):
                    # 检查函数前是否已有装饰器
                    if i > 0 and "@retry" not in lines[i-1]:
                        modified_lines.append("    @retry(max_tries=3, delay=2, backoff=2, exceptions=(Exception,))")
                modified_lines.append(line)
                i += 1
            
            # 更新文件内容
            new_content = "\n".join(modified_lines)
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"✅ 已为 {file_path} 添加重试机制")
                modified = True
    
    if not modified:
        print("⚠️ 未找到需要添加重试机制的函数")

def check_dns_settings():
    """检查DNS设置"""
    print("\n检查DNS设置...")
    try:
        with open("/etc/resolv.conf", "r") as f:
            resolv_conf = f.read()
            print("当前DNS配置:")
            print(resolv_conf)
        
        # 检查是否使用公共DNS
        if "8.8.8.8" not in resolv_conf and "1.1.1.1" not in resolv_conf:
            print("建议添加公共DNS服务器以提高可靠性")
            print("可以添加以下内容到/etc/resolv.conf:")
            print("nameserver 8.8.8.8")
            print("nameserver 1.1.1.1")
    except Exception as e:
        print(f"无法读取DNS配置: {str(e)}")

def restart_application():
    """重启应用"""
    print("\n重启应用...")
    try:
        # 查找Python进程
        result = subprocess.run(["ps", "aux"], 
                              stdout=subprocess.PIPE, 
                              text=True)
        
        main_process = None
        for line in result.stdout.splitlines():
            if "main.py" in line and "python" in line:
                main_process = line
                break
        
        if main_process:
            print(f"找到主进程: {main_process}")
            # 提取PID
            pid = None
            parts = main_process.split()
            if len(parts) > 1:
                try:
                    pid = int(parts[1])
                except ValueError:
                    pass
            
            if pid:
                print(f"正在停止进程 {pid}...")
                subprocess.run(["kill", str(pid)], check=True)
                print(f"✅ 进程 {pid} 已停止")
            else:
                print("❌ 无法提取进程ID")
        else:
            print("⚠️ 未找到运行中的主进程")
        
        # 启动应用
        print("正在启动应用...")
        subprocess.Popen(["nohup", "python3", "main.py", ">", "/dev/null", "2>&1", "&"], 
                        start_new_session=True)
        print("✅ 应用已启动")
        
        # 等待几秒钟
        time.sleep(5)
        
        # 检查应用是否成功启动
        result = subprocess.run(["ps", "aux"], 
                              stdout=subprocess.PIPE, 
                              text=True)
        
        app_running = False
        for line in result.stdout.splitlines():
            if "main.py" in line and "python" in line:
                app_running = True
                print(f"✅ 应用成功启动: {line}")
                break
        
        if not app_running:
            print("❌ 应用启动失败")
    except Exception as e:
        print(f"重启应用出错: {str(e)}")

def main():
    """主函数"""
    print("===== NiubiAI Bot 网络错误修复工具 =====")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")
    
    # 执行修复步骤
    check_python_version()
    check_network_connectivity()
    check_proxy_settings()
    update_httpx_package()
    update_python_telegram_bot()
    modify_request_timeout()
    add_retry_mechanism()
    check_dns_settings()
    
    # 询问是否重启应用
    print("\n所有修复步骤已完成")
    restart = input("是否要重启应用? (y/n): ").strip().lower()
    if restart == "y":
        restart_application()
    
    print(f"\n结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("===== 修复完成 =====")

if __name__ == "__main__":
    main()
EOF

# 上传修复脚本
echo -e "${YELLOW}上传网络修复脚本到服务器...${NC}" | tee -a "$LOG_FILE"
scp_upload "fix_network.py" "$SERVER_USER@$SERVER_IP:$APP_DIR/fix_network.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}上传脚本失败!${NC}" | tee -a "$LOG_FILE"
    exit 1
fi

# 设置执行权限
ssh_command "chmod +x $APP_DIR/fix_network.py"

# 执行修复脚本
echo -e "${GREEN}执行网络修复脚本...${NC}" | tee -a "$LOG_FILE"
ssh_command "cd $APP_DIR && python3 fix_network.py"

# 检查应用状态
echo -e "${BLUE}检查应用状态...${NC}" | tee -a "$LOG_FILE"
ssh_command "ps aux | grep python"

echo -e "${GREEN}===== 网络错误修复完成 =====${NC}" | tee -a "$LOG_FILE"
echo -e "${BLUE}结束时间: $(date)${NC}" | tee -a "$LOG_FILE"
echo -e "${YELLOW}日志已保存到: $LOG_FILE${NC}"