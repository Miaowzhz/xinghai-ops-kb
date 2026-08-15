# backend/app/services/guardrail_service.py
import re
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rule import GuardrailRule
from app.schemas.rule import RuleCreate, RuleUpdate

_rule_cache: tuple[float, list[GuardrailRule]] | None = None
CACHE_TTL = 60  # 规则缓存 60 秒，兼顾性能与修改生效速度


async def _load_enabled_rules(db: AsyncSession) -> list[GuardrailRule]:
    global _rule_cache
    now = time.time()
    if _rule_cache and now - _rule_cache[0] < CACHE_TTL:
        return _rule_cache[1]
    stmt = select(GuardrailRule).where(GuardrailRule.enabled.is_(True))
    rules = list((await db.execute(stmt)).scalars())
    _rule_cache = (now, rules)
    return rules


def invalidate_cache() -> None:
    global _rule_cache
    _rule_cache = None


def _is_hit(rule: GuardrailRule, question: str) -> bool:
    if rule.match_type == "keyword":
        return rule.pattern in question
    try:
        return re.search(rule.pattern, question) is not None
    except re.error:
        return False  # 规则配置的正则写错了，不能让整个问答挂掉


async def match_block_rule(db: AsyncSession, question: str) -> GuardrailRule | None:
    """返回第一条命中的 block 规则；未命中返回 None。"""
    for rule in await _load_enabled_rules(db):
        if rule.action == "block" and _is_hit(rule, question):
            return rule
    return None


async def match_confirm_rules(db: AsyncSession, question: str) -> list[GuardrailRule]:
    return [
        rule for rule in await _load_enabled_rules(db)
        if rule.action == "confirm" and _is_hit(rule, question)
    ]


async def list_rules(db: AsyncSession) -> list[GuardrailRule]:
    stmt = select(GuardrailRule).order_by(GuardrailRule.id)
    return list((await db.execute(stmt)).scalars())


async def create_rule(db: AsyncSession, body: RuleCreate, admin_id: int) -> GuardrailRule:
    rule = GuardrailRule(**body.model_dump(), created_by=admin_id)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    invalidate_cache()
    return rule


async def update_rule(
    db: AsyncSession, rule_id: int, body: RuleUpdate
) -> GuardrailRule | None:
    rule = await db.get(GuardrailRule, rule_id)
    if not rule:
        return None
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    invalidate_cache()
    return rule
