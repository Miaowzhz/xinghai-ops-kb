import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Form, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.config import settings
from app.core.deps import require_admin
from app.database import get_db
from app.models.chunk import KgDocumentChunk
from app.models.document import KgDocument
from app.models.user import User
from app.schemas.document import DocumentItem
from app.services import ingest_service

# 文档路由聚合
router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}


def _save_upload(file: UploadFile) -> tuple[str, int, str]:
    """校验扩展名并落盘到 uploads/，返回 (相对路径, 文件大小字节, 扩展名)。

    upload 与 reingest 共用同一套保存逻辑。
    """
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PDF / DOCX / MD / TXT 格式")
    # uuid 前缀防止文件名冲突和路径注入
    save_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
    file_path = os.path.join("uploads", save_name)
    file_bytes = file.file.read()
    with open(os.path.join(settings.BASE_DIR, file_path), "wb") as f:
        f.write(file_bytes)
    return file_path, len(file_bytes), ext


def _purge_chunks(db: Session, doc: KgDocument) -> None:
    """清掉旧 chunk 的两处数据（Milvus 向量 + MySQL 行），保留 kg_document 行。"""
    chunks = db.scalars(
        select(KgDocumentChunk).where(KgDocumentChunk.document_id == doc.id)).all()
    ingest_service.delete_from_milvus([c.milvus_id for c in chunks if c.milvus_id])
    for c in chunks:
        db.delete(c)


@router.post("/upload")
def upload_file(
        background_tasks: BackgroundTasks,
        file: UploadFile,
        title: str = Form(...),
        doc_type: str = Form(...),
        product_line: str = Form(...),
        product_version: str = Form(...),
        db: Session = Depends(get_db),
        admin: User = Depends(require_admin),
):
    """上传文件"""
    # 查重（同title + product_line 拒绝），先查重再落盘避免留下孤儿文件
    exists = db.scalar(select(KgDocument).where(
        KgDocument.title == title, KgDocument.product_line == product_line))
    if exists is not None:
        raise HTTPException(status_code=409, detail="已存在同名文档，请使用重新上传新版")

    # 原始文件落地，逻辑与 reingest 共用
    file_path, file_size, ext = _save_upload(file)

    doc = KgDocument(
        title=title, doc_type=doc_type, product_line=product_line,
        product_version=product_version, file_path=file_path, file_type=ext,
        file_size=file_size,
        status="pending", created_by=admin.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(ingest_service.run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status}


# 删除与 reingest
@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    doc = db.get(KgDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status == "parsing":
        raise HTTPException(status_code=409, detail="文档正在入库中，请稍后再删除")
    ingest_service.delete_document_everywhere(db, doc)
    return {"doc_id": doc_id, "deleted": True}


@router.post("/{doc_id}/reingest")
def reingest_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    product_version: str = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = db.get(KgDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status == "parsing":
        raise HTTPException(status_code=409, detail="文档正在入库中，请稍后再操作")
    # 1) 新文件覆盖保存  2) 清掉旧 chunk 的两处数据  3) 回 pending 重走流水线
    new_path, new_file_size, new_ext = _save_upload(file)  # 与 upload 相同的落盘逻辑
    _purge_chunks(db, doc)                                 # 只清 chunk 两处，保留 kg_document 行
    # 新文件已用新 uuid 落盘，删掉旧文件避免 uploads/ 残留
    old_abs = os.path.join(settings.BASE_DIR, doc.file_path)
    if os.path.exists(old_abs):
        os.remove(old_abs)
    doc.file_path, doc.file_type = new_path, new_ext
    doc.file_size = new_file_size  # 新文件大小（字节）
    doc.product_version = product_version
    doc.version += 1
    doc.status = "pending"
    doc.chunk_count = 0
    db.commit()
    background_tasks.add_task(ingest_service.run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status, "version": doc.version}
