#!/bin/bash

# 更新NiubiAI Bot到Python 3.12
# 作者: AI助手
# 日期: 2024-07-10

set -e

# 颜色定义
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 项目路径
PROJECT_DIR="/opt/niubiai"
BACKUP_DIR="/opt/niubiai_backup_$(date +%Y%m%d_%H%M%S)"

# 检查是否为root用户
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}开始更新NiubiAI Bot到Python 3.12...${NC}"

# 步骤1: 备份当前项目
echo -e "${YELLOW}步骤1: 备份当前项目到 $BACKUP_DIR${NC}"
mkdir -p "$BACKUP_DIR"
cp -r "$PROJECT_DIR"/* "$BACKUP_DIR"/
echo -e "${GREEN}✓ 备份完成${NC}"

# 步骤2: 安装Python 3.12
echo -e "${YELLOW}步骤2: 安装Python 3.12${NC}"
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils

# 安装pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
echo -e "${GREEN}✓ Python 3.12安装完成${NC}"

# 步骤3: 创建新的虚拟环境
echo -e "${YELLOW}步骤3: 创建新的虚拟环境${NC}"
cd "$PROJECT_DIR"
python3.12 -m venv venv_py312
source venv_py312/bin/activate

# 步骤4: 安装新的依赖
echo -e "${YELLOW}步骤4: 安装新的依赖${NC}"
pip install --upgrade pip
pip install -r requirements.py312.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 步骤5: 更新启动脚本
echo -e "${YELLOW}步骤5: 更新启动脚本${NC}"
cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv_py312/bin/activate
python main.py
EOF

chmod +x "$PROJECT_DIR/start.sh"
echo -e "${GREEN}✓ 启动脚本更新完成${NC}"

# 步骤6: 更新服务文件（如果使用systemd）
if [ -f "/etc/systemd/system/niubiai.service" ]; then
    echo -e "${YELLOW}步骤6: 更新systemd服务文件${NC}"
    cat > "/etc/systemd/system/niubiai.service" << EOF
[Unit]
Description=NiubiAI Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv_py312/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    echo -e "${GREEN}✓ 服务文件更新完成${NC}"
fi

# 步骤7: 停止当前服务
echo -e "${YELLOW}步骤7: 停止当前服务${NC}"
pkill -f "python3 main.py" || true
if [ -f "/etc/systemd/system/niubiai.service" ]; then
    systemctl stop niubiai.service || true
fi
echo -e "${GREEN}✓ 服务已停止${NC}"

# 步骤8: 启动新服务
echo -e "${YELLOW}步骤8: 启动新服务${NC}"
if [ -f "/etc/systemd/system/niubiai.service" ]; then
    systemctl start niubiai.service
    systemctl status niubiai.service
else
    cd "$PROJECT_DIR"
    nohup ./start.sh > /dev/null 2>&1 &
    echo -e "${GREEN}✓ 服务已在后台启动${NC}"
fi

echo -e "${GREEN}NiubiAI Bot已成功更新到Python 3.12!${NC}"
echo -e "${YELLOW}提示: 如果遇到问题，可以从备份 $BACKUP_DIR 恢复${NC}"