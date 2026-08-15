import json
from datetime import datetime
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import KgDocument
from app.models.feedback import AuditTask, QaFeedback
from app.models.qa import QaMessage
from app.schemas.feedback import ResolveRequest


async def find_question_message(db, answer_msg: QaMessage) -> QaMessage | None:
    """取被点踩答案对应的原始问题：优先 reply_to_id 精确关联，取不到回退时间序推导。"""
    if answer_msg.reply_to_id:
        question = await db.get(QaMessage, answer_msg.reply_to_id)
        if question and question.role == "user":
            return question
    # 回退：同 session 内该答案之前最后一条 user 消息（兼容没有 reply_to_id 的历史数据）
    stmt = (
        select(QaMessage)
        .where(
            QaMessage.session_id == answer_msg.session_id,
            QaMessage.role == "user",
            QaMessage.id < answer_msg.id,
        )
        .order_by(desc(QaMessage.id))
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_tasks(
    db: AsyncSession, status: str | None, page: int, page_size: int
) -> tuple[list[AuditTask], int]:
    filters = [AuditTask.status == status] if status else []
    total_stmt = select(func.count(AuditTask.id)).where(*filters)
    total = int((await db.execute(total_stmt)).scalar_one())
    stmt = (
        select(AuditTask)
        .where(*filters)
        .order_by(desc(AuditTask.created_at), desc(AuditTask.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list((await db.execute(stmt)).scalars()), total


async def get_task_detail(db: AsyncSession, task_id: int) -> dict | None:
    task = await db.get(AuditTask, task_id)
    if task is None:
        return None

    answer = await db.get(QaMessage, task.message_id)
    feedback = await db.get(QaFeedback, task.feedback_id)
    if answer is None or feedback is None:
        return None

    question = await find_question_message(db, answer)
    try:
        citations = json.loads(answer.citations) if answer.citations else None
    except (TypeError, json.JSONDecodeError):
        citations = None

    document_ids = {
        item.get("document_id")
        for item in citations or []
        if isinstance(item, dict) and item.get("document_id") is not None
    }
    existing_document_ids: set[int] = set()
    if document_ids:
        document_stmt = select(KgDocument.id).where(KgDocument.id.in_(document_ids))
        existing_document_ids = set((await db.execute(document_stmt)).scalars())

    return {
        "id": task.id,
        "feedback_id": task.feedback_id,
        "message_id": task.message_id,
        "status": task.status,
        "resolution": task.resolution,
        "resolved_by": task.resolved_by,
        "resolved_at": task.resolved_at,
        "created_at": task.created_at,
        "question": question.content if question else "原始问题已不可用",
        "answer": answer.content,
        "message_status": answer.status,
        "citations": citations,
        "dislike_reason": feedback.reason,
        "document_deleted": bool(document_ids - existing_document_ids),
    }


async def resolve_task(
    db: AsyncSession, task_id: int, admin_id: int, body: ResolveRequest
) -> AuditTask | str:
    # 1. 带状态条件的 UPDATE（乐观锁思想）：
    #    只有当前仍是 pending 的任务才允许流转，resolved/rejected 不可回退
    stmt = (
        update(AuditTask)
        .where(AuditTask.id == task_id, AuditTask.status == "pending")
        .values(
            status=body.status,
            resolution=body.resolution,
            resolved_by=admin_id,
            resolved_at=datetime.utcnow(),
        )
    )
    result = await db.execute(stmt)

    if result.rowcount == 0:
        # 没更新到任何行：要么任务不存在，要么已被别人处理
        exists = await db.get(AuditTask, task_id)
        return "not_found" if not exists else "already_resolved"

    # 2. 同一事务联动关闭关联反馈
    task = await db.get(AuditTask, task_id)
    fb_stmt = (
        update(QaFeedback)
        .where(QaFeedback.id == task.feedback_id)
        .values(status="resolved")
    )
    await db.execute(fb_stmt)

    await db.commit()
    await db.refresh(task)
    return task
