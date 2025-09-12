#!/bin/bash

# NiubiAI Bot - sshpass安装和脚本权限设置
# 作者: AI助手
# 日期: 2024-07-10

set -e

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 显示脚本说明
echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}      NiubiAI Bot - sshpass安装和脚本权限设置${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 检查操作系统
if [[ "$(uname)" == "Darwin" ]]; then
    OS="macOS"
elif [[ "$(uname)" == "Linux" ]]; then
    OS="Linux"
    if [ -f /etc/debian_version ]; then
        DISTRO="Debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="RedHat"
    fi
else
    echo -e "${RED}不支持的操作系统: $(uname)${NC}"
    exit 1
fi

echo -e "${YELLOW}检测到操作系统: $OS${NC}"

# 安装sshpass
echo -e "\n${YELLOW}安装sshpass...${NC}"

if [[ "$OS" == "macOS" ]]; then
    if command -v brew &> /dev/null; then
        echo -e "${YELLOW}使用Homebrew安装sshpass...${NC}"
        brew install hudochenkov/sshpass/sshpass || {
            echo -e "${RED}安装失败，尝试添加tap后重新安装...${NC}"
            brew tap hudochenkov/sshpass
            brew install hudochenkov/sshpass/sshpass
        }
    else
        echo -e "${RED}未检测到Homebrew，请先安装Homebrew: https://brew.sh/${NC}"
        exit 1
    fi
elif [[ "$OS" == "Linux" ]]; then
    if [[ "$DISTRO" == "Debian" ]]; then
        echo -e "${YELLOW}使用apt安装sshpass...${NC}"
        sudo apt-get update
        sudo apt-get install -y sshpass
    elif [[ "$DISTRO" == "RedHat" ]]; then
        echo -e "${YELLOW}使用yum安装sshpass...${NC}"
        sudo yum install -y sshpass
    else
        echo -e "${RED}不支持的Linux发行版${NC}"
        exit 1
    fi
fi

# 检查sshpass是否安装成功
if command -v sshpass &> /dev/null; then
    echo -e "${GREEN}✓ sshpass安装成功${NC}"
    sshpass -V
else
    echo -e "${RED}sshpass安装失败${NC}"
    exit 1
fi

# 设置脚本执行权限
echo -e "\n${YELLOW}设置脚本执行权限...${NC}"
SCRIPTS=(
    "deploy_with_sshpass.sh"
    "one_click_deploy.sh"
    "monitor_with_sshpass.sh"
    "restart_service.sh"
    "view_logs.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo -e "${GREEN}✓ 已设置 $script 为可执行${NC}"
    else
        echo -e "${YELLOW}警告: $script 不存在，跳过${NC}"
    fi
done

# 完成
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}      安装和设置完成!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}现在您可以使用以下脚本:${NC}"
echo -e "- ./deploy_with_sshpass.sh  (完整部署脚本)"
echo -e "- ./one_click_deploy.sh     (一键部署脚本)"
echo -e "- ./monitor_with_sshpass.sh (远程监控脚本)"
echo -e "- ./restart_service.sh      (服务重启脚本)"
echo -e "- ./view_logs.sh            (日志查看脚本)"