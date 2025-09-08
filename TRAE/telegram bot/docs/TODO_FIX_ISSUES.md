# 问题修复待办事项清单

## 待解决的问题

### 1. 数据库连接配置
- **问题描述**: 部分测试由于数据库连接配置问题失败
- **影响范围**: 涉及数据库操作的测试
- **解决方案**: 
  1. 为测试环境配置SQLite或PostgreSQL数据库
  2. 安装必要的数据库驱动程序(如asyncpg)
  3. 创建专门的测试配置文件
  4. 隔离测试环境和生产环境的配置

### 2. SQLAlchemy异步驱动
- **问题描述**: SQLAlchemy需要异步驱动程序来支持异步操作
- **影响范围**: 数据库相关操作
- **解决方案**:
  1. 安装asyncpg驱动: `pip install asyncpg`
  2. 更新数据库URL格式为异步格式: `postgresql+asyncpg://...`
  3. 验证异步数据库连接

### 3. 测试环境完善
- **问题描述**: 测试环境配置不完整
- **影响范围**: 所有涉及外部依赖的测试
- **解决方案**:
  1. 创建.test.env配置文件
  2. 配置Redis测试实例
  3. 设置测试数据库
  4. 配置测试日志系统

### 4. pytest-asyncio版本监控
- **问题描述**: pytest-asyncio插件版本可能再次出现兼容性问题
- **影响范围**: 测试运行
- **解决方案**:
  1. 定期检查pytest和pytest-asyncio版本兼容性
  2. 在CI/CD管道中固定兼容的版本组合
  3. 建立版本更新测试机制

## 操作指引

### 配置测试数据库
1. 安装PostgreSQL或使用SQLite
2. 创建测试数据库:
   ```sql
   CREATE DATABASE test_telegram_bot_db;
   ```
3. 更新.test.env文件中的数据库配置:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/test_telegram_bot_db
   ```

### 安装异步数据库驱动
```bash
pip install asyncpg
```

### 运行完整测试套件
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_products.py -v
```

### 配置测试环境
1. 复制.env.example为.test.env:
   ```bash
   cp .env.example .test.env
   ```
2. 修改.test.env中的配置项以适应测试环境
3. 在测试运行时指定环境文件:
   ```bash
   ENVIRONMENT=test python -m pytest tests/
   ```

### 维护pytest-asyncio兼容性
1. 固定兼容的版本组合:
   ```bash
   pip install pytest==8.4.2 pytest-asyncio==0.21.1
   ```
2. 定期检查版本更新:
   ```bash
   pip list | grep pytest
   ```
3. 在requirements.txt中指定版本:
   ```
   pytest==8.4.2
   pytest-asyncio==0.21.1
   ```

## 优先级排序

### 高优先级
1. 数据库连接配置 - 影响核心功能测试
2. SQLAlchemy异步驱动 - 影响数据库操作性能
3. pytest-asyncio版本监控 - 防止再次出现兼容性问题

### 中优先级
4. 测试环境完善 - 影响测试覆盖率
5. 增加更多测试用例 - 提升代码质量保证

### 低优先级
6. CI/CD管道配置 - 提升开发效率
7. 代码质量检查工具配置 - 提升代码规范性

## 负责人建议

建议由后端开发团队负责数据库连接配置和异步驱动安装，由测试团队负责测试环境完善和测试用例补充。DevOps团队可以协助配置CI/CD管道。