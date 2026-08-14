import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guardrail import GuardrailRule


async def match_block_rule(db: AsyncSession, question: str) -> GuardrailRule | None:
    rules = await db.scalars(select(GuardrailRule).where(
        GuardrailRule.enabled == 1,
        GuardrailRule.action == 'block',
    ))
    for rule in rules:
        try:
            matched = re.search(rule.pattern, question, flags=re.IGNORECASE)
        except re.error:
            matched = rule.pattern.lower() in question.lower()
        if matched:
            return rule
    return None
