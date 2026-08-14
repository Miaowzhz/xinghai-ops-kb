from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.database import get_db
from app.models.feedback import QaFeedback
from app.models.qa import QaMessage, QaSession
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter(prefix='/api/feedback', tags=['feedback'])


@router.post('', response_model=FeedbackOut)
async def create_feedback(body: FeedbackCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if body.feedback_type == 'dislike' and not body.reason.strip():
        raise HTTPException(status_code=422, detail='请填写点踩原因，方便管理员定位问题')
    message = await db.scalar(
        select(QaMessage)
        .join(QaSession, QaSession.id == QaMessage.session_id)
        .where(QaMessage.id == body.message_id, QaSession.user_id == user.id)
    )
    if message is None or message.status not in ('normal', 'refused'):
        raise HTTPException(status_code=400, detail='该回答当前不支持反馈')
    feedback = await db.scalar(select(QaFeedback).where(
        QaFeedback.message_id == body.message_id,
        QaFeedback.user_id == user.id,
    ))
    if feedback is None:
        feedback = QaFeedback(message_id=body.message_id, user_id=user.id)
        db.add(feedback)
    feedback.feedback_type = body.feedback_type
    feedback.reason = body.reason.strip() if body.reason else None
    feedback.status = 'pending' if body.feedback_type == 'dislike' else 'resolved'
    await db.commit()
    await db.refresh(feedback)
    return feedback
