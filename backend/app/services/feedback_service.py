from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.qa import QaMessage
from app.models.feedback import QaFeedback, AuditTask
from app.schemas.feedback import FeedbackCreate


async def submit_feedback(
    db: AsyncSession, user_id: int, body: FeedbackCreate
) -> QaFeedback:
    # 1. 基本校验：消息必须存在且是 assistant 消息；点踩必填原因
    message = await db.get(QaMessage, body.message_id)
    if not message or message.role != "assistant":
        raise HTTPException(status_code=404, detail="消息不存在或不支持反馈")
    # 只允许评价 normal / refused 的答案；blocked 是固定拦截话术、failed 没有内容，都无可评之物
    if message.status == "blocked":
        raise HTTPException(status_code=422, detail="护栏拦截的拦截话术无需评价")
    if message.status == "failed":
        raise HTTPException(status_code=422, detail="生成失败的消息没有内容可评价")
    if body.feedback_type == "dislike" and not (body.reason and body.reason.strip()):
        raise HTTPException(status_code=422, detail="点踩必须填写原因")

    # 2. 查已有反馈：唯一约束 message_id + user_id 兜底
    stmt = select(QaFeedback).where(
        QaFeedback.message_id == body.message_id,
        QaFeedback.user_id == user_id,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        # 3a. 重复提交：按"旧类型 → 新类型"分流，同一事务内完成联动
        old_type, new_type = existing.feedback_type, body.feedback_type
        if old_type == new_type:
            # 同类型：只更新原因，不动任务
            existing.reason = body.reason
        elif old_type == "like" and new_type == "dislike":
            # 赞转踩：补插审核任务，反馈置回 pending
            existing.feedback_type = "dislike"
            existing.reason = body.reason
            existing.status = "pending"
            db.add(AuditTask(
                feedback_id=existing.id,
                message_id=body.message_id,
                status="pending",
            ))
        else:
            # 踩转赞：关联的 pending 任务置 rejected（用户撤销点踩），反馈置 resolved
            existing.feedback_type = "like"
            existing.reason = body.reason
            existing.status = "resolved"
            await db.execute(
                update(AuditTask)
                .where(
                    AuditTask.feedback_id == existing.id,
                    AuditTask.status == "pending",  # 只关还没处理的；已有结论的任务不回退
                )
                .values(
                    status="rejected",
                    resolution="用户撤销点踩",
                    resolved_at=datetime.utcnow(),
                )
            )
        await db.commit()
        await db.refresh(existing)
        return existing

    # 3b. 首次提交：反馈与审核任务在同一事务，要么都成功要么都回滚
    feedback = QaFeedback(
        message_id=body.message_id,
        user_id=user_id,
        feedback_type=body.feedback_type,
        reason=body.reason,
        # like 落库即 resolved（只统计不审核）；dislike 置 pending 等待审核
        status="resolved" if body.feedback_type == "like" else "pending",
    )
    db.add(feedback)
    await db.flush()  # 先拿到 feedback.id，同事务内可见，但不提交

    if body.feedback_type == "dislike":
        task = AuditTask(
            feedback_id=feedback.id,
            message_id=body.message_id,
            status="pending",
        )
        db.add(task)

    await db.commit()      # 到这里两张表才一起真正落库
    await db.refresh(feedback)
    return feedback