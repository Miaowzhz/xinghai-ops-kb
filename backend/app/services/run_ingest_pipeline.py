# backend/app/services/ingest_service.py（流水线主函数）
import asyncio
import traceback
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.document import KgDocument
from app.models.chunk import KgDocumentChunk
from app.services.ingest_service import write_to_milvus
from app.utils.parsers import parse_file
from app.utils.chunking import split_document


async def run_ingest_pipeline(doc_id: int) -> None:
    """上传后在后台执行：解析 → 切块 → MySQL → Milvus，状态机 pending→parsing→success/failed。"""
    async with AsyncSessionLocal() as db:
        try:
            doc = await db.get(KgDocument, doc_id)
            if doc is None or doc.status != "pending":
                return  # 文档被删除或状态已变化，直接放弃
            doc.status = "parsing"
            await db.commit()

            text = await asyncio.to_thread(
                parse_file, f"{settings.BASE_DIR}/{doc.file_path}", doc.file_type
            )
            if not text.strip():
                raise ValueError("未解析到文本内容，请确认不是纯图片扫描件")

            chunks = split_document(text, doc.doc_type)

            # 1) chunk 先落 MySQL，拿到自增 chunk_id 作为两处存储的关联键
            rows = []
            for idx, content in enumerate(chunks, start=1):
                row = KgDocumentChunk(
                    document_id=doc.id, chunk_index=idx, content=content,
                    product_line=doc.product_line, product_version=doc.product_version,
                )
                db.add(row)
                rows.append(row)
            await db.flush()  # 分配 id，不提交事务

            # 2) 向量化写 Milvus（实现见 §8.2）
            milvus_ids = await asyncio.to_thread(write_to_milvus, rows)
            for row, mid in zip(rows, milvus_ids):
                row.milvus_id = mid

            doc.status = "success"
            doc.chunk_count = len(rows)
            doc.fail_reason = None
            await db.commit()
        except Exception as exc:
            await db.rollback()
            await _mark_failed(doc_id, f"{exc}"[:500])
            traceback.print_exc()


async def _mark_failed(doc_id: int, reason: str) -> None:
    async with AsyncSessionLocal() as db:
        doc = await db.get(KgDocument, doc_id)
        if doc is not None:
            doc.status = "failed"
            doc.fail_reason = reason
            await db.commit()
