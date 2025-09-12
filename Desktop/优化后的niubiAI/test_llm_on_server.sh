#!/bin/bash

# NiubiAI LLM模型服务器测试脚本
# 用于连接到服务器并测试LLM模型能否成功对接和输出

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 服务器信息
SERVER_USER="root"
SERVER_HOST="103.115.64.72"
SERVER_PORT="22"
REMOTE_DIR="/opt/niubiai"

# 检查sshpass是否安装
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}sshpass未安装，尝试安装...${NC}"
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        brew install hudochenkov/sshpass/sshpass || {
            echo -e "${RED}安装失败，尝试添加tap后重新安装...${NC}"
            brew tap hudochenkov/sshpass
            brew install hudochenkov/sshpass/sshpass
        }
    elif [[ "$(uname)" == "Linux" ]]; then
        # Linux
        if [ -f /etc/debian_version ]; then
            sudo apt-get update && sudo apt-get install -y sshpass
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y sshpass
        else
            echo -e "${RED}无法确定Linux发行版，请手动安装sshpass${NC}"
            exit 1
        fi
    else
        echo -e "${RED}无法确定操作系统类型，请手动安装sshpass${NC}"
        exit 1
    fi

    # 再次检查是否安装成功
    if ! command -v sshpass &> /dev/null; then
        echo -e "${RED}sshpass安装失败，请手动安装后再运行此脚本${NC}"
        exit 1
    fi
    echo -e "${GREEN}sshpass安装成功${NC}"
fi

# 从环境变量或配置文件获取密码
if [ -n "$SSH_PASSWORD" ]; then
    # 使用环境变量中的密码
    SERVER_PASSWORD="$SSH_PASSWORD"
    echo -e "${GREEN}使用环境变量中的密码${NC}"
elif [ -f "$HOME/.ssh/niubiai_password" ]; then
    # 使用配置文件中的密码
    SERVER_PASSWORD=$(cat "$HOME/.ssh/niubiai_password")
    echo -e "${GREEN}使用配置文件中的密码${NC}"
else
    # 使用脚本中的默认密码
    SERVER_PASSWORD="pnooZZMV7257"
    echo -e "${GREEN}使用默认密码${NC}"
fi

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI LLM模型服务器测试脚本${NC}"
echo -e "${YELLOW}==================================================${NC}"
echo -e "此脚本将执行以下操作："
echo -e "1. 上传LLM测试脚本到服务器"
echo -e "2. 在服务器上执行测试脚本"
echo -e "3. 显示测试结果"
echo -e "${YELLOW}==================================================${NC}"
echo

# 确认操作
read -p "是否继续？(y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

# 上传测试脚本
echo -e "\n${YELLOW}步骤1: 上传LLM测试脚本到服务器${NC}"
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -P $SERVER_PORT "$(pwd)/test_llm_model.py" "$SERVER_USER@$SERVER_HOST:$REMOTE_DIR/test_llm_model.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}上传测试脚本失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 测试脚本上传成功${NC}"

# 设置执行权限
echo -e "\n${YELLOW}步骤2: 设置测试脚本执行权限${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SERVER_PORT "$SERVER_USER@$SERVER_HOST" "chmod +x $REMOTE_DIR/test_llm_model.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}设置执行权限失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 执行权限设置成功${NC}"

# 检查服务器环境
echo -e "\n${YELLOW}步骤3: 检查服务器环境${NC}"
echo -e "${YELLOW}检查Python版本和依赖...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SERVER_PORT "$SERVER_USER@$SERVER_HOST" "cd $REMOTE_DIR && python3 --version && pip3 list | grep -E 'openai|anthropic|google-generativeai'"

echo -e "\n${YELLOW}检查应用进程状态...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SERVER_PORT "$SERVER_USER@$SERVER_HOST" "ps aux | grep -E 'python|niubiai' | grep -v grep"

# 执行测试脚本
echo -e "\n${YELLOW}步骤4: 在服务器上执行测试脚本${NC}"
echo -e "${YELLOW}测试所有LLM模型配置...${NC}"
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -p $SERVER_PORT "$SERVER_USER@$SERVER_HOST" "cd $REMOTE_DIR && python3 test_llm_model.py --all --check-api"
if [ $? -ne 0 ]; then
    echo -e "${RED}测试脚本执行失败${NC}"
    exit 1
fi

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      NiubiAI LLM模型测试完成!${NC}"
echo -e "${GREEN}==================================================${NC}"

exit 0