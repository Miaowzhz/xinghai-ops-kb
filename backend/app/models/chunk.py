# backend/app/models/chunk.py
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class KgDocumentChunk(Base):
    __tablename__ = "kg_document_chunk"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # 即 chunk_id
    document_id: Mapped[int] = mapped_column(ForeignKey("kg_document.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)      # 在文档内的顺序
    content: Mapped[str] = mapped_column(Text)             # chunk 全文，引用溯源用
    product_line: Mapped[str] = mapped_column(String(64))  # 冗余自文档，检索过滤用
    product_version: Mapped[str] = mapped_column(String(64))
    milvus_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)