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
from app.schemas.document import DocumentDetail, DocumentListResponse, DocumentItem
from app.services import ingest_service
from app.services.run_ingest_pipeline import run_ingest_pipeline

# 文档路由聚合
router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}


def _document_payload(doc: KgDocument, created_by_name: str) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "product_line": doc.product_line,
        "product_version": doc.product_version,
        "status": doc.status,
        "fail_reason": doc.fail_reason,
        "chunk_count": doc.chunk_count,
        "version": doc.version,
        "created_by_name": created_by_name,
        "created_at": doc.created_at,
    }


def _save_upload(file: UploadFile) -> tuple[str, int, str]:
    """校验扩展名并落盘，返回 (相对路径, 文件大小字节, 扩展名)。

    upload 与 reingest 共用同一套保存逻辑。
    """
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PDF / DOCX / MD / TXT 格式")
    # uuid 前缀防止文件名冲突和路径注入
    save_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
    upload_dir = os.path.normpath(settings.UPLOAD_DIR)
    file_path = os.path.join(upload_dir, save_name)
    upload_root = os.path.join(settings.BASE_DIR, upload_dir)
    os.makedirs(upload_root, exist_ok=True)
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

# 上传知识文档
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

    background_tasks.add_task(run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status}

# 查询知识文档列表
@router.get("", response_model=DocumentListResponse)
def get_documents(
        page: int = 1,
        page_size: int = 10,
        doc_type: str | None = None,
        product_line: str | None = None,
        status: str | None = None,
        db: Session = Depends(get_db),
        user: User = Depends(require_admin)
):
    # 1) 先拼过滤条件，count 和列表共用一份
    conds = []
    if doc_type is not None:
        conds.append(KgDocument.doc_type == doc_type)
    if product_line is not None:
        conds.append(KgDocument.product_line == product_line)
    if status is not None:
        conds.append(KgDocument.status == status)
    # 若业务要求"只看自己上传的"，加上这一条：
    # conds.append(KgDocument.created_by == user.id)

    # 2) total 基于未分页的过滤结果统计
    total = db.scalar(select(func.count(KgDocument.id)).where(*conds)) or 0

    # 3) 列表：join sys_user 取上传人姓名 + 稳定排序 + 分页
    stmt = (
        select(KgDocument, User.display_name.label("created_by_name"))
        .join(User, KgDocument.created_by == User.id)
        .where(*conds)
        .order_by(KgDocument.created_at.desc(), KgDocument.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    # 查的是 (KgDocument, display_name) 元组，不能用 db.scalars()
    items = [DocumentItem(**_document_payload(row[0], row.created_by_name))
             for row in db.execute(stmt).all()]
    return DocumentListResponse(total=total, items=items)

# 文档详情
@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document_detail(doc_id: int, db: Session = Depends(get_db),
                        user: User = Depends(require_admin)):
    row = db.execute(
        select(KgDocument, User.display_name.label("created_by_name"))
        .join(User, KgDocument.created_by == User.id)
        .where(KgDocument.id == doc_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc, created_by_name = row
    return DocumentDetail(**_document_payload(doc, created_by_name),
                          file_type=doc.file_type, updated_at=doc.updated_at)


# 删除
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


# 重新入库
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
    background_tasks.add_task(run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status, "version": doc.version}
