# 简化的测试服务器
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 设置环境变量
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'

# 创建应用
app = FastAPI(
    title="股票分析API - 测试版",
    description="K线图功能测试",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
try:
    from stock_analysis_api.api.routes.chart_routes import router as chart_router
    from stock_analysis_api.api.routes.comprehensive_analysis import router as analysis_router
    app.include_router(chart_router)
    app.include_router(analysis_router)
    print("✅ 图表路由加载成功")
    print("✅ 综合分析路由加载成功")
except Exception as e:
    print(f"❌ 路由加载失败: {e}")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "股票分析API测试服务器",
        "status": "running",
        "features": [
            "综合K线图+技术分析",
            "LLM智能分析解读",
            "技术指标详细分析",
            "批量股票分析",
            "投资建议生成"
        ],
        "endpoints": {
            "comprehensive": "/analysis/comprehensive/{symbol}",
            "quick_analysis": "/analysis/quick/{symbol}",
            "batch_analysis": "/analysis/batch",
            "indicators": "/analysis/indicators/{symbol}",
            "chart_styles": "/chart/styles",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "stock-analysis-api"}

if __name__ == "__main__":
    import uvicorn
    print("启动股票分析API测试服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
