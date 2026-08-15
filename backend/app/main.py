# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.auth import router as auth_router
from app.router.document import router as document_router
from app.router.qa import router as qa_router
from app.router.guardrail import router as guardrail_router
from app.router.feedback import router as feedback_router

app = FastAPI(title="星海运维智能知识库")

# 开发期允许 Vite 前端（localhost:5173）跨域直调；走 vite 代理时其实不会触发跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(qa_router)
app.include_router(guardrail_router)
app.include_router(feedback_router)


@app.get("/api/health")
def health():
    """健康检查：能返回说明 FastAPI 与路由注册正常。"""
    return {"status": "ok"}
