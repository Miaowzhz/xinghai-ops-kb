# backend/app/models/feedback_service.py
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class QaFeedback(Base):
    __tablename__ = "qa_feedback"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_feedback_message_user"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("qa_message.id"), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"))
    feedback_type: Mapped[str] = mapped_column(String(10))   # like / dislike
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)  # 点踩原因
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AuditTask(Base):
    __tablename__ = "audit_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("qa_feedback.id"))
    message_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("qa_message.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending 待处理 / resolved 已解决 / rejected 误点驳回
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)  # 处理结论
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )