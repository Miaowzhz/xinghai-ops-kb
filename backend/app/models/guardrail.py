from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class GuardrailRule(Base):
    __tablename__ = 'guardrail_rule'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(128))
    rule_type: Mapped[str] = mapped_column(String(32))
    match_type: Mapped[str] = mapped_column(String(16))
    pattern: Mapped[str] = mapped_column(String(512))
    action: Mapped[str] = mapped_column(String(16))
    reply_text: Mapped[str] = mapped_column(Text)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
