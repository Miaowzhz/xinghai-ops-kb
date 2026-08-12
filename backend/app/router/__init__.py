from fastapi import APIRouter

from app.router.endpoints import health

# 全项目 API 统一挂载在 /api 下（main.py 中 include_router(prefix="/api")）
# 例如：文档列表 GET /api/documents、问答 POST /api/qa/chat、健康检查 GET /api/health
api_router = APIRouter()
api_router.include_router(health.router)
