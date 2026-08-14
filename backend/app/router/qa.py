# backend/app/routers/qa.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.qa import SessionCreate, SessionOut, MessageOut
from app.services import qa_service

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/sessions", response_model=SessionOut)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await qa_service.create_session(db, user.id, body.title or "新会话")


@router.get("/sessions", response_model=list[SessionOut])
async def get_sessions(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await qa_service.list_sessions(db, user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await qa_service.list_messages(db, session_id, user.id)