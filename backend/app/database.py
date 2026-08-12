"""
SQLAlchemy engine / SessionLocal / Base / get_db

异步 SQLAlchemy：使用 asyncmy 驱动连接 MySQL，配合 FastAPI 的
依赖注入（get_db）为每个请求提供一个数据库会话。
"""
# backend/app/database.py
from datetime import datetime
from sqlalchemy import create_engine, DateTime
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, Mapped, mapped_column
from app.config import settings

engine = create_engine(settings.MYSQL_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 SQLAlchemy 模型的基类（models/ 下的模型都继承它）。"""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

def get_db():
    """FastAPI 依赖：每个请求一个 Session，请求结束自动关闭。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()