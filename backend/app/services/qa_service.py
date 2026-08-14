# backend/app/services/qa_service.py
import json
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.qa import QaSession, QaMessage

HISTORY_LIMIT = 10  # 多轮对话只带最近 10 条消息，防止上下文爆炸


async def create_session(db: AsyncSession, user_id: int, title: str = "新会话") -> QaSession:
    session = QaSession(user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user_id: int) -> list[dict]:
    """按最近活跃时间倒序返回会话列表，并派生每个会话的消息数（P06 列表展示用）。"""
    stmt = (
        select(QaSession, func.count(QaMessage.id).label("message_count"))
        .outerjoin(QaMessage, QaMessage.session_id == QaSession.id)
        .where(QaSession.user_id == user_id)
        .group_by(QaSession.id)
        .order_by(desc(QaSession.updated_at))
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "message_count": cnt,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s, cnt in rows
    ]


async def list_messages(db: AsyncSession, session_id: int, user_id: int) -> list[QaMessage]:
    await _check_session_owner(db, session_id, user_id)  # 越权访问直接 404/403
    stmt = select(QaMessage).where(QaMessage.session_id == session_id).order_by(QaMessage.id)
    messages = list((await db.execute(stmt)).scalars())
    for message in messages:
        message.citations = json.loads(message.citations) if message.citations else None
    return messages


async def load_history(db: AsyncSession, session_id: int) -> list[dict]:
    """读取该会话最近 10 条消息，组装成 LangGraph state 里的 history。"""
    stmt = (
        select(QaMessage)
        .where(QaMessage.session_id == session_id)
        .order_by(desc(QaMessage.id))
        .limit(HISTORY_LIMIT)
    )
    rows = list((await db.execute(stmt)).scalars())
    rows.reverse()  # 倒序取出后翻回正序
    return [{"role": m.role, "content": m.content} for m in rows]


async def save_message(
    db: AsyncSession,
    session_id: int,
    role: str,
    content: str,
    status: str = "normal",
    citations: list[dict] | None = None,
    guardrail_rule_id: int | None = None,
    reply_to_id: int | None = None,
) -> QaMessage:
    msg = QaMessage(
        session_id=session_id,
        role=role,
        content=content,
        status=status,
        citations=json.dumps(citations, ensure_ascii=False) if citations else None,
        guardrail_rule_id=guardrail_rule_id,
        reply_to_id=reply_to_id,
    )
    db.add(msg)
    # 回写会话活跃时间：P06 会话列表按 updated_at 倒序，新增消息必须刷新它
    session = await db.get(QaSession, session_id)
    session.updated_at = datetime.now()
    await db.commit()
    await db.refresh(msg)
    return msg
