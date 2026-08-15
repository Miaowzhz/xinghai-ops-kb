# backend/app/routers/guardrail.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import require_admin
from app.schemas.rule import RuleCreate, RuleUpdate, RuleOut
from app.services import guardrail_service

router = APIRouter(
    prefix="/api/guardrail",
    tags=["guardrail"],
    dependencies=[Depends(require_admin)],  # 整个路由仅 admin 可访问
)


@router.get("/rules", response_model=list[RuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    return await guardrail_service.list_rules(db)


@router.post("/rules", response_model=RuleOut)
async def create_rule(
    body: RuleCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    return await guardrail_service.create_rule(db, body, admin.id)


@router.put("/rules/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: int,
    body: RuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    rule = await guardrail_service.update_rule(db, rule_id, body)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule