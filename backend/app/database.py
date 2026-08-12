"""
SQLAlchemy engine / SessionLocal / Base / get_db

异步 SQLAlchemy：使用 asyncmy 驱动连接 MySQL，配合 FastAPI 的
依赖注入（get_db）为每个请求提供一个数据库会话。
"""

from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings

# 异步引擎：连接串在 config.py 中配置（mysql+asyncmy://...）
# pool_pre_ping 避免 MySQL 空闲连接被回收后导致"连接已断开"错误
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 会话工厂：expire_on_commit=False，commit 后对象属性仍可访问
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的公共基类（声明式基类）。"""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：为单个请求提供一个数据库会话。

    请求结束后自动关闭会话并归还连接池。
    """
    async with SessionLocal() as session:
        yield session
