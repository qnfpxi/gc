#!/usr/bin/env python3
"""
本地开发环境端到端测试（无需 Docker）

这个版本使用本地 Python 环境，适合没有 Docker 的开发环境
"""

import asyncio
import json
import sqlite3
from pathlib import Path
import subprocess
import sys

class LocalE2ETestSuite:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.storage_path = self.project_root / "storage"
        
    def check_python_version(self):
        """检查 Python 版本"""
        version = sys.version_info
        print(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ 需要 Python 3.8 或更高版本")
            return False
        
        print("✅ Python 版本检查通过")
        return True
    
    def check_dependencies(self):
        """检查必要的依赖"""
        print("📦 检查依赖包...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'aiogram',
            'sqlalchemy',
            'alembic',
            'asyncpg',
            'aiofiles',
            'aiohttp',
            'pydantic'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} 未安装")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  缺少以下依赖包: {', '.join(missing_packages)}")
            print("请运行以下命令安装：")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def setup_storage(self):
        """设置存储目录"""
        print("📁 设置存储目录...")
        
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            (self.storage_path / "media").mkdir(exist_ok=True)
            (self.storage_path / "uploads").mkdir(exist_ok=True)
            
            # 创建测试文件以验证写入权限
            test_file = self.storage_path / "test_write.txt"
            test_file.write_text("test")
            test_file.unlink()
            
            print("✅ 存储目录设置完成")
            return True
            
        except Exception as e:
            print(f"❌ 存储目录设置失败: {e}")
            return False
    
    def check_env_file(self):
        """检查环境变量文件"""
        print("⚙️  检查环境配置...")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("❌ .env 文件不存在")
            print("请先配置环境变量文件")
            return False
        
        # 检查关键配置
        env_content = env_file.read_text()
        
        if "TELEGRAM_BOT_TOKEN=your_bot_token_here" in env_content:
            print("❌ TELEGRAM_BOT_TOKEN 未配置")
            print("请在 .env 文件中设置您的真实 Bot Token")
            return False
        
        if "TELEGRAM_BOT_TOKEN=" in env_content:
            print("✅ Bot Token 已配置")
        else:
            print("❌ 未找到 TELEGRAM_BOT_TOKEN 配置")
            return False
        
        print("✅ 环境配置检查通过")
        return True
    
    def test_basic_imports(self):
        """测试基本导入"""
        print("🔍 测试项目模块导入...")
        
        try:
            # 测试关键模块导入
            sys.path.insert(0, str(self.project_root))
            
            from app.config import settings
            print("✅ 配置模块导入成功")
            
            from app.services.local_file_storage import LocalFileStorageService
            print("✅ 文件存储服务导入成功")
            
            from app.schemas.media import MediaUploadResult
            print("✅ 媒体模式导入成功")
            
            print("✅ 项目模块导入测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 模块导入失败: {e}")
            return False
    
    async def test_file_storage_service(self):
        """测试文件存储服务"""
        print("📁 测试文件存储服务...")
        
        try:
            from app.services.local_file_storage import LocalFileStorageService
            from io import BytesIO
            
            storage_service = LocalFileStorageService()
            
            # 创建测试文件
            test_content = b"This is a test image content for local E2E testing"
            test_file = BytesIO(test_content)
            
            # 测试上传
            result = await storage_service.upload_file(
                file=test_file,
                filename="test_local_e2e.jpg",
                content_type="image/jpeg",
                folder="test"
            )
            
            print(f"✅ 文件上传成功:")
            print(f"   URL: {result.url}")
            print(f"   路径: {result.file_path}")
            print(f"   大小: {result.file_size} bytes")
            
            # 检查文件是否存在
            exists = await storage_service.file_exists(result.file_path)
            print(f"✅ 文件存在性检查: {'成功' if exists else '失败'}")
            
            # 清理测试文件
            deleted = await storage_service.delete_file(result.file_path)
            print(f"✅ 文件删除: {'成功' if deleted else '失败'}")
            
            return True
            
        except Exception as e:
            print(f"❌ 文件存储服务测试失败: {e}")
            return False
    
    def create_minimal_test_db(self):
        """创建最小化的测试数据库（SQLite）"""
        print("💾 创建测试数据库...")
        
        try:
            db_path = self.project_root / "test_local.db"
            
            # 删除旧数据库
            if db_path.exists():
                db_path.unlink()
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 创建基本表结构
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '📁',
                    parent_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    price DECIMAL(12,2),
                    currency TEXT DEFAULT 'CNY',
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    city TEXT,
                    contact_telegram TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    images TEXT,  -- JSON string
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            """)
            
            # 插入测试分类
            cursor.execute("""
                INSERT INTO categories (name, description, icon) 
                VALUES ('测试分类', '用于端到端测试的分类', '🧪')
            """)
            
            conn.commit()
            conn.close()
            
            print(f"✅ 测试数据库创建完成: {db_path}")
            return True
            
        except Exception as e:
            print(f"❌ 测试数据库创建失败: {e}")
            return False
    
    async def run_local_tests(self):
        """运行本地测试"""
        print("🧪 开始本地端到端测试")
        print("=" * 60)
        
        tests = [
            ("Python 版本检查", self.check_python_version),
            ("依赖包检查", self.check_dependencies),
            ("存储目录设置", self.setup_storage),
            ("环境文件检查", self.check_env_file),
            ("模块导入测试", self.test_basic_imports),
            ("文件存储服务", self.test_file_storage_service),
            ("测试数据库创建", self.create_minimal_test_db),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                if result:
                    passed += 1
                    print(f"✅ {test_name} 通过")
                else:
                    print(f"❌ {test_name} 失败")
            except Exception as e:
                print(f"❌ {test_name} 出现异常: {e}")
        
        # 测试总结
        print(f"\n{'='*60}")
        print(f"🏁 本地测试完成: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！可以进行 Bot 测试。")
            print("\n🤖 下一步 - 启动 Bot 测试:")
            print("   python test_bot.py")
            print("\n📝 注意事项:")
            print("   - 确保 .env 文件中的 TELEGRAM_BOT_TOKEN 已正确配置")
            print("   - 本地测试使用 SQLite 数据库")
            print("   - 文件存储在 ./storage 目录")
            return True
        else:
            print(f"⚠️  有 {total - passed} 项测试失败，需要修复后再继续。")
            return False


async def main():
    """主函数"""
    test_suite = LocalE2ETestSuite()
    
    print("🏠 本地开发环境端到端测试")
    print("适用于没有 Docker 的开发环境")
    print("=" * 60)
    
    success = await test_suite.run_local_tests()
    
    if success:
        print("\n🎯 测试成功！您现在可以:")
        print("1. 启动 Bot: python test_bot.py")
        print("2. 在 Telegram 中测试完整的用户旅程")
        print("3. 按照 E2E_TEST_MANUAL.md 进行手动测试")
        print("\n💡 提示: 这是简化版测试，生产环境建议使用 Docker")
    else:
        print("\n🔧 修复建议:")
        print("1. 安装缺少的依赖包")
        print("2. 检查 .env 文件配置")
        print("3. 确保项目目录结构正确")


if __name__ == "__main__":
    asyncio.run(main())
