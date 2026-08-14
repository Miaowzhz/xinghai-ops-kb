# backend/app/models/qa.py
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class QaSession(Base):
    __tablename__ = "qa_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="新会话")  # 首条问题截断生成，与 04 DDL VARCHAR(255) 一致
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class QaMessage(Base):
    __tablename__ = "qa_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("qa_session.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))          # user / assistant
    content: Mapped[str] = mapped_column(Text)             # 问题或完整答案
    citations: Mapped[str | None] = mapped_column(Text, nullable=True)  # 引用 JSON 数组
    status: Mapped[str] = mapped_column(String(20), default="normal")
    # normal 正常 / blocked 护栏拦截 / refused 无依据拒答 / failed 系统失败
    guardrail_rule_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 命中的 block 护栏规则 id
    reply_to_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)        # assistant 消息对应的 user 消息 id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)