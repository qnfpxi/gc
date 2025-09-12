# NiubiAI Bot - sshpass部署指南

## 概述

本文档提供了使用sshpass远程部署和管理NiubiAI Bot的详细指南。通过这些脚本，您可以轻松地在本地机器上管理远程服务器上的NiubiAI Bot。

## 准备工作

在开始使用这些脚本之前，请确保：

1. 已安装sshpass工具
2. 所有脚本具有执行权限

您可以使用提供的`setup_sshpass.sh`脚本自动完成这些准备工作：

```bash
./setup_sshpass.sh
```

## 脚本说明

### 1. 部署脚本

#### 完整部署脚本 (deploy_with_sshpass.sh)

此脚本提供了交互式的部署过程，包括备份、文件上传、执行升级脚本和检查部署结果等步骤。

使用方法：
```bash
./deploy_with_sshpass.sh
```

功能：
- 备份服务器上的项目
- 上传Python 3.12升级文件
- 设置脚本执行权限
- 选择部署方式（直接升级或Docker部署）
- 检查部署结果
- 运行兼容性测试

#### 一键部署脚本 (one_click_deploy.sh)

此脚本提供了简化的一键部署过程，自动执行所有必要的步骤。

使用方法：
```bash
./one_click_deploy.sh
```

功能：
- 自动备份服务器上的项目
- 上传必要的升级文件
- 执行升级脚本
- 检查部署结果

### 2. 监控脚本 (monitor_with_sshpass.sh)

此脚本用于实时监控服务器上NiubiAI Bot的运行状态。

使用方法：
```bash
./monitor_with_sshpass.sh
```

功能：
- 检查进程状态
- 检查系统资源（CPU、内存、磁盘）
- 检查最新日志和错误日志
- 检查Python版本
- 每30秒自动刷新（按Ctrl+C退出）

### 3. 服务重启脚本 (restart_service.sh)

此脚本用于远程重启NiubiAI Bot服务。

使用方法：
```bash
./restart_service.sh
```

功能：
- 检查当前服务状态
- 提供多种重启方式选择：
  - 重启Python进程
  - 重启Docker容器
  - 重启系统服务
- 检查重启后的服务状态和日志

### 4. 日志查看脚本 (view_logs.sh)

此脚本用于远程查看NiubiAI Bot的日志。

使用方法：
```bash
./view_logs.sh
```

功能：
- 查看最新日志（最后50行）
- 实时监控日志（按Ctrl+C退出）
- 查看错误日志
- 搜索日志内容
- 下载日志文件到本地

## 常见问题解决

### 1. sshpass安装失败

如果`setup_sshpass.sh`脚本无法安装sshpass，您可以尝试手动安装：

- macOS：
  ```bash
  brew tap hudochenkov/sshpass
  brew install hudochenkov/sshpass/sshpass
  ```

- Debian/Ubuntu：
  ```bash
  sudo apt-get update
  sudo apt-get install -y sshpass
  ```

- CentOS/RHEL：
  ```bash
  sudo yum install -y sshpass
  ```

### 2. 连接失败

如果脚本无法连接到服务器，请检查：

- 服务器IP地址是否正确
- 用户名和密码是否正确
- 服务器是否允许SSH密码登录
- 网络连接是否正常

### 3. 权限问题

如果脚本执行时出现权限问题，请确保所有脚本都有执行权限：

```bash
chmod +x *.sh
```

## 安全注意事项

1. 这些脚本中包含服务器密码，请确保脚本文件的安全，不要将其分享给未授权的人员。

2. 建议在使用完毕后，从脚本中删除密码信息，或者将脚本文件设置为只有您可以访问：

   ```bash
   chmod 700 *.sh
   ```

3. 更安全的做法是使用SSH密钥认证而不是密码认证，但这需要额外的配置。

## 联系支持

如果在使用这些脚本过程中遇到任何问题，请联系技术支持团队获取帮助。

---

文档创建日期：2024-07-10  
作者：AI助手