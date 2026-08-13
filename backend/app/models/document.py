# backend/app/models/document.py
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KgDocument(Base):
    __tablename__ = "kg_document"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(16))      # manual / case / sop / api
    product_line: Mapped[str] = mapped_column(String(64))  # 如 ECS、VPC、RDS
    product_version: Mapped[str] = mapped_column(String(64))  # 如 V3.2
    file_path: Mapped[str] = mapped_column(String(512))    # uploads/ 下的相对路径
    file_type: Mapped[str] = mapped_column(String(8))      # pdf / docx / md / txt
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)  # 原始文件大小（字节）
    status: Mapped[str] = mapped_column(String(16), default="pending")
    # pending 待入库 / parsing 入库中 / success 成功 / failed 失败
    fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)  # reingest 一次 +1
    created_by: Mapped[int] = mapped_column()              # 上传人 sys_user.id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)