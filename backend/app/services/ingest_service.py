import os
from dashscope import TextEmbedding
from pymilvus import MilvusClient
from sqlalchemy import select, func
from app.config import settings
from app.models.chunk import KgDocumentChunk
from app.models.document import KgDocument
from app.models.user import User
from app.schemas.document import DocumentItem

_milvus = MilvusClient(uri=settings.MILVUS_URI)          # collection: ops_kb_chunks
EMBEDDING_DIM = 1024                                     # text-embedding-v3


def _embed(texts: list[str]) -> list[list[float]]:
    """批量调 DashScope text-embedding-v3，返回 1024 维向量列表；失败抛异常由流水线兜底。"""
    resp = TextEmbedding.call(
        model="text-embedding-v3", input=texts,
        api_key=settings.DASHSCOPE_API_KEY,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Embedding 调用失败：{resp.message}")
    return [item["embedding"] for item in resp.output["embeddings"]]


def write_to_milvus(rows: list) -> list[str]:
    """向量 + 标量字段 upsert 进 Milvus，主键用 MySQL 的 chunk_id，重复写不产生重复数据。"""
    vectors = _embed([r.content for r in rows])
    data = [
        {
            # fix: KgDocumentChunk.id 是 int，而 Milvus 初始化脚本中明确把 chunk_id 定义成了 VARCHAR
            "chunk_id": str(r.id),                      # 标量主键，与 MySQL 对账
            "dense": vector,                       # 1024 维
            "content": r.content,                  # BM25 Function 输入字段
            "product_line": r.product_line,        # 检索过滤字段
            "product_version": r.product_version,  # 检索过滤字段
        }
        for r, vector in zip(rows, vectors)
    ]
    _milvus.upsert(collection_name="ops_kb_chunks", data=data)
    return [str(r.id) for r in rows]  # milvus_id 即 chunk_id 的字符串形式


def delete_from_milvus(milvus_ids: list[str]) -> None:
    if milvus_ids:
        _milvus.delete(collection_name="ops_kb_chunks", ids=list(milvus_ids))


def delete_document_everywhere(db, doc: KgDocument) -> None:
    """以 MySQL 的 chunk 记录为账本，清掉 Milvus / uploads 文件 / 两张表的行。"""
    chunks = db.scalars(
        select(KgDocumentChunk).where(KgDocumentChunk.document_id == doc.id)).all()
    delete_from_milvus([c.milvus_id for c in chunks if c.milvus_id])
    for c in chunks:
        db.delete(c)
    abs_path = os.path.join(settings.BASE_DIR, doc.file_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)
    db.delete(doc)
    db.commit()


def list_documents(db, doc_type=None, product_line=None, status=None,
                   page: int = 1, page_size: int = 10) -> dict:
    """分页 + 条件过滤查文档列表；join sys_user 把上传人 id 转成展示姓名 created_by_name。"""
    stmt = (
        select(KgDocument, User.display_name.label("created_by_name"))
        .join(User, User.id == KgDocument.created_by)
        .order_by(KgDocument.created_at.desc())
    )
    if doc_type:
        stmt = stmt.where(KgDocument.doc_type == doc_type)
    if product_line:
        stmt = stmt.where(KgDocument.product_line == product_line)
    if status:
        stmt = stmt.where(KgDocument.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        {**DocumentItem.model_validate(doc).model_dump(), "created_by_name": name}
        for doc, name in rows
    ]
    return {"total": total, "items": items}