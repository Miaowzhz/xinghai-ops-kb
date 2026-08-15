# backend/app/routers/audit.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_admin
from app.schemas.feedback import AuditTaskOut, AuditTaskDetail, ResolveRequest
from app.services import audit_service

router = APIRouter(
    prefix="/api/audit",
    tags=["audit"],
    dependencies=[Depends(require_admin)],  # 审核相关接口仅 admin
)


@router.get("/tasks", response_model=dict)
async def list_tasks(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await audit_service.list_tasks(db, status, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/tasks/{task_id}", response_model=AuditTaskDetail)
async def task_detail(task_id: int, db: AsyncSession = Depends(get_db)):
    detail = await audit_service.get_task_detail(db, task_id)
    if not detail:
        raise HTTPException(status_code=404, detail="审核任务不存在")
    return detail


@router.post("/tasks/{task_id}/resolve", response_model=AuditTaskOut)
async def resolve_task(
    task_id: int,
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    result = await audit_service.resolve_task(db, task_id, admin.id, body)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="审核任务不存在")
    if result == "already_resolved":
        raise HTTPException(status_code=409, detail="任务已被处理")
    return result