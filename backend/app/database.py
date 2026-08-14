"""SQLAlchemy 异步 engine / session / Base / FastAPI database dependency."""
# backend/app/database.py
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings

async_url = settings.MYSQL_URL.replace("mysql+pymysql://", "mysql+asyncmy://", 1)
engine = create_async_engine(async_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """所有 SQLAlchemy 模型的基类（models/ 下的模型都继承它）。"""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

async def get_db():
    """FastAPI 依赖：每个请求一个 AsyncSession，请求结束自动关闭。"""
    async with AsyncSessionLocal() as db:
        yield db
