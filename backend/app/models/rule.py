# backend/app/models/rule.py
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class GuardrailRule(Base):
    __tablename__ = "guardrail_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(64))
    rule_type: Mapped[str] = mapped_column(String(20))   # sensitive_op / high_risk_cmd / price
    action: Mapped[str] = mapped_column(String(10))      # block / confirm
    match_type: Mapped[str] = mapped_column(String(10))  # keyword / regex
    pattern: Mapped[str] = mapped_column(String(512))    # 关键词或正则
    reply_text: Mapped[str] = mapped_column(Text)        # 拦截话术
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )