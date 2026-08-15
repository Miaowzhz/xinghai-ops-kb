# backend/app/routers/feedback_service.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.services import feedback_service

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut)
async def submit_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await feedback_service.submit_feedback(db, user.id, body)