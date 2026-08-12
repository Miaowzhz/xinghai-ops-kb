# backend/app/models/user.py
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(16))  # engineer / admin
    status: Mapped[str] = mapped_column(String(16), default="enabled")  # enabled / disabled，disabled 禁止登录
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)