# NiubiAI Bot - Python 3.12 升级指南

## 概述

本文档提供了将NiubiAI Bot从Python 3.10升级到Python 3.12的详细指南。升级到Python 3.12可以带来性能提升、更好的错误处理和最新的语言特性支持。

## 准备工作

在开始升级之前，请确保：

1. 已备份所有重要数据和配置文件
2. 有足够的服务器权限（需要root权限）
3. 服务器有稳定的网络连接
4. 有足够的磁盘空间（至少需要1GB空闲空间）

## 升级方法

我们提供了两种升级方法，您可以根据自己的需求选择其中一种：

### 方法一：直接在服务器上升级（推荐）

这种方法适用于直接在服务器上运行NiubiAI Bot的情况。

1. 将以下文件上传到服务器的`/opt/niubiai`目录：
   - `requirements.py312.txt`（更新的依赖列表）
   - `update_to_python312.sh`（升级脚本）

2. 给脚本添加执行权限：
   ```bash
   chmod +x /opt/niubiai/update_to_python312.sh
   ```

3. 运行升级脚本：
   ```bash
   cd /opt/niubiai
   ./update_to_python312.sh
   ```

4. 脚本会自动完成以下操作：
   - 备份当前项目
   - 安装Python 3.12
   - 创建新的虚拟环境
   - 安装更新的依赖
   - 更新启动脚本
   - 更新systemd服务文件（如果存在）
   - 重启服务

### 方法二：使用Docker部署

如果您希望使用Docker来部署NiubiAI Bot，可以使用这种方法。

1. 将以下文件上传到服务器的`/opt/niubiai`目录：
   - `Dockerfile.py312`（基于Python 3.12的Dockerfile）
   - `requirements.py312.txt`（更新的依赖列表）
   - `deploy_docker_py312.sh`（Docker部署脚本）

2. 给脚本添加执行权限：
   ```bash
   chmod +x /opt/niubiai/deploy_docker_py312.sh
   ```

3. 运行部署脚本：
   ```bash
   cd /opt/niubiai
   ./deploy_docker_py312.sh
   ```

4. 脚本会自动完成以下操作：
   - 备份当前配置
   - 准备Docker构建文件
   - 构建Docker镜像
   - 停止并移除旧容器
   - 启动新容器
   - 检查容器状态

## 兼容性测试

在完成升级后，建议运行兼容性测试脚本，确保所有功能正常工作：

1. 将`test_py312_compatibility.py`上传到服务器的`/opt/niubiai`目录

2. 运行测试脚本：
   ```bash
   cd /opt/niubiai
   python3.12 test_py312_compatibility.py
   ```

3. 检查测试结果，确保所有测试都通过

## 常见问题解决

### 1. 依赖安装失败

如果某些依赖安装失败，可以尝试单独安装：

```bash
# 激活虚拟环境
source /opt/niubiai/venv_py312/bin/activate

# 安装特定依赖
pip install <依赖包名>
```

### 2. 服务启动失败

如果服务启动失败，请检查日志文件：

```bash
# 如果使用systemd
journalctl -u niubiai.service -n 50

# 或者查看日志文件
cat /opt/niubiai/logs/niubiai.log
```

### 3. 恢复备份

如果需要恢复到之前的版本，可以使用备份：

```bash
# 停止当前服务
pkill -f "python main.py" || true
systemctl stop niubiai.service || true

# 恢复备份
rm -rf /opt/niubiai/*
cp -r /opt/niubiai_backup_<备份时间戳>/* /opt/niubiai/

# 重启服务
systemctl start niubiai.service || nohup python3 /opt/niubiai/main.py > /dev/null 2>&1 &
```

## 注意事项

1. **数据库兼容性**：Python 3.12与SQLAlchemy 2.0.x和asyncpg 0.29.x兼容，不需要修改数据库代码。

2. **API兼容性**：已更新OpenAI、Anthropic和Google Generative AI的客户端库到最新版本，确保与最新API兼容。

3. **性能优化**：Python 3.12提供了更好的性能，特别是在异步操作和字符串处理方面，这对NiubiAI Bot的响应速度有积极影响。

4. **监控**：升级后，请密切监控服务的运行状况和日志，确保一切正常。

## 联系支持

如果在升级过程中遇到任何问题，请联系技术支持团队获取帮助。

---

文档创建日期：2024-07-10  
作者：AI助手