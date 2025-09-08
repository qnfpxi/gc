#!/usr/bin/env python3
"""
简化API服务器启动脚本
用于快速测试API端点
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_dependencies():
    """检查核心依赖"""
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'aiofiles',
        'jose',
        'passlib',
        'bcrypt'
    ]
    
    print("🚀 启动简化API服务器")
    print("=" * 50)
    print("📦 检查依赖包...")
    
    missing_deps = []
    for dep in dependencies:
        try:
            if dep == 'jose':
                importlib.util.find_spec('jose')
            elif dep == 'bcrypt':
                importlib.util.find_spec('bcrypt')
            else:
                importlib.util.find_spec(dep)
            print(f"✅ {dep}")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep}")
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖: {', '.join(missing_deps)}")
        print("请运行: pip install " + " ".join(missing_deps))
        return False
    
    return True

def check_config():
    """检查配置"""
    print("\n🔧 检查配置...")
    
    # 检查.env文件
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 文件存在")
    else:
        print("⚠️  .env 文件不存在，将使用默认配置")
    
    # 检查基本配置
    api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8001')
    print(f"✅ API_BASE_URL: {api_base_url}")
    
    # 检查数据库配置
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print("✅ Database configured: True")
    else:
        print("⚠️  Database not configured")
    
    print("\n✅ 环境检查通过")
    return True

def main():
    """主函数"""
    if not check_dependencies():
        sys.exit(1)
    
    if not check_config():
        sys.exit(1)
    
    # 启动服务器
    print("🌐 启动API服务器...")
    print("📍 地址: http://localhost:8001")
    print("📖 文档: http://localhost:8001/docs")
    print("\n按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 动态导入并启动FastAPI应用
    try:
        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # 导入FastAPI应用
        from app.main import app
        import uvicorn
        
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8001,  # 使用8001端口避免冲突
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()