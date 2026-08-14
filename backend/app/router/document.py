"""
知识库文档管理 API 路由模块
============================

提供知识文档的全生命周期管理接口：
- 上传新文档（含查重与异步入库流水线）
- 分页查询文档列表（支持多条件过滤）
- 查询单文档详情
- 删除文档（含向量库 + 数据库 + 本地文件的联动清理）
- 重新上传新版本（清理旧 chunk 与旧文件，重走入库流水线）

所有写操作（上传/删除/重传）均通过 require_admin 依赖限制为管理员角色，
读操作同样仅管理员可见，若后续需开放给普通工程师可改为 require_login。
"""

import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Form, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.deps import require_admin
from app.database import get_db
from app.models.chunk import KgDocumentChunk
from app.models.document import KgDocument
from app.models.user import User
from app.schemas.document import DocumentDetail, DocumentListResponse, DocumentItem
from app.services import ingest_service
from app.services.run_ingest_pipeline import run_ingest_pipeline

# FastAPI 路由聚合器：统一前缀 + Swagger UI 分组标签
router = APIRouter(prefix="/api/documents", tags=["documents"])

# 允许上传的文件扩展名白名单（小写），与前端 DocumentUploadView 保持一致
ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}


def _document_payload(doc: KgDocument, created_by_name: str) -> dict:
    """将 KgDocument ORM 模型 + 上传人姓名拼装为接口返回的通用字典。

    列表接口与详情接口共用此函数，避免字段两处漂移。
    注意：详情接口需要额外追加 file_type、updated_at，在外层补齐。

    Args:
        doc: 数据库查询出的 KgDocument 实例
        created_by_name: 通过 join User 表拿到的 display_name，避免 N+1 查询

    Returns:
        字段与 DocumentItem / DocumentDetail Schema 对齐的字典
    """
    return {
        "id": doc.id,                          # 文档主键 ID
        "title": doc.title,                    # 文档标题（业务唯一：同 product_line 下不可重复）
        "doc_type": doc.doc_type,              # 文档类型：操作手册/故障案例/架构文档 等
        "product_line": doc.product_line,      # 所属产品线
        "product_version": doc.product_version,# 产品版本号
        "status": doc.status,                  # 入库状态：pending / parsing / success / failed
        "fail_reason": doc.fail_reason,        # 入库失败时的错误信息，成功时为 None
        "chunk_count": doc.chunk_count,        # 切分后已写入向量库的 chunk 数量
        "version": doc.version,                # 文档版本号，每次 reingest 自增 1
        "created_by_name": created_by_name,    # 上传人显示名（非 ID，前端直接展示）
        "created_at": doc.created_at,          # 首次上传时间（datetime）
    }


def _save_upload(file: UploadFile) -> tuple[str, int, str]:
    """校验扩展名并落盘，返回 (相对路径, 文件大小字节, 扩展名)。

    upload 与 reingest 共用同一套保存逻辑，避免两处重复代码。

    安全设计：
    - 扩展名白名单校验（拒绝可疑类型）
    - 文件名用 os.path.basename 剥离目录，防止路径注入攻击
    - 文件名前加 uuid 前缀，保证并发上传不冲突、不覆盖

    Args:
        file: FastAPI UploadFile 对象，来自 multipart/form-data 请求体

    Returns:
        file_path:  相对 BASE_DIR 的存储路径，直接存入 KgDocument.file_path
        file_size:  文件字节数，用于展示上传大小
        ext:        小写扩展名，用于选择后续解析器（pdf/docx/md/txt）

    Raises:
        HTTPException 400: 扩展名不在白名单时抛出
    """
    # 从文件名末尾取扩展名并统一小写，空文件名无扩展名则视为 ""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PDF / DOCX / MD / TXT 格式")

    # uuid 前缀 + basename：同时解决"同名文件覆盖"与"路径注入（../../etc/passwd）"两个问题
    save_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"

    # settings.UPLOAD_DIR 可能是相对路径，用 normpath 去掉多余分隔符
    upload_dir = os.path.normpath(settings.UPLOAD_DIR)
    # 相对路径（存数据库）：uploads/uuid_xxx.pdf
    file_path = os.path.join(upload_dir, save_name)
    # 绝对路径（建目录用）：BASE_DIR/uploads/
    upload_root = os.path.join(settings.BASE_DIR, upload_dir)
    os.makedirs(upload_root, exist_ok=True)

    # 一次性读入内存再落盘（当前知识文档体积可控；若后续支持大文件需改分块流式写入）
    file_bytes = file.file.read()
    with open(os.path.join(settings.BASE_DIR, file_path), "wb") as f:
        f.write(file_bytes)
    return file_path, len(file_bytes), ext


async def _purge_chunks(db: AsyncSession, doc: KgDocument) -> None:
    """清掉旧 chunk 的两处数据（Milvus 向量 + MySQL 行），保留 kg_document 行。

    仅在 reingest 重传场景调用；完全删除文档走 ingest_service.delete_document_everywhere。

    清理顺序有讲究：先删 Milvus 向量（外部依赖可能失败），再删 MySQL 行。
    若先删了 MySQL 却没删 Milvus，会导致 Milvus 出现"僵尸向量"无法回溯。

    Args:
        db:  SQLAlchemy Session 事务上下文，调用方负责 commit
        doc: 目标文档，取其 id 查询关联 chunks
    """
    # 1) 查出该文档下所有 chunk 记录（含 milvus_id 字段）
    chunks = (await db.scalars(
        select(KgDocumentChunk).where(KgDocumentChunk.document_id == doc.id))).all()

    # 2) 先删向量库 Milvus（外部依赖，失败可重试）——过滤掉 milvus_id 为空的脏数据
    ingest_service.delete_from_milvus([c.milvus_id for c in chunks if c.milvus_id])

    # 3) 再删 MySQL 中的 chunk 行（本事务内，随外层 commit 生效）
    for c in chunks:
        await db.delete(c)

# ---------------------------------------------------------------------------
# 上传知识文档接口
# 设计要点：先查重再落盘（避免"拒绝后磁盘仍留孤儿文件"）；入库流水线异步执行。
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_file(
        background_tasks: BackgroundTasks,  # FastAPI 后台任务：入库流水线在响应后异步跑
        file: UploadFile,                   # 用户上传的文件体（multipart/form-data）
        title: str = Form(...),             # 文档标题（同 product_line 下唯一）
        doc_type: str = Form(...),          # 文档类型（前端枚举下拉）
        product_line: str = Form(...),      # 所属产品线
        product_version: str = Form(...),   # 产品版本号
        db: AsyncSession = Depends(get_db), # SQLAlchemy AsyncSession（请求级事务）
        admin: User = Depends(require_admin),  # 权限拦截：仅管理员可上传
):
    """上传新知识文档。

    状态流转：pending -> 后台异步 parsing -> success / failed
    解析耗时可能数秒到数分钟，前端轮询 GET /api/documents/{id} 获取进度。
    """
    # ---------- 1. 业务查重：同 title + product_line 视为重复文档 ----------
    # 注意先查重再落盘，否则"重名被拒绝但文件已写入 uploads/"会产生孤儿文件
    exists = await db.scalar(select(KgDocument).where(
        KgDocument.title == title, KgDocument.product_line == product_line))
    if exists is not None:
        raise HTTPException(status_code=409, detail="已存在同名文档，请使用重新上传新版")

    # ---------- 2. 原始文件落盘（与 reingest 共用保存逻辑） ----------
    file_path, file_size, ext = _save_upload(file)

    # ---------- 3. 写 kg_document 行，状态初始化为 pending ----------
    doc = KgDocument(
        title=title, doc_type=doc_type, product_line=product_line,
        product_version=product_version, file_path=file_path, file_type=ext,
        file_size=file_size,
        status="pending",   # 等待后台任务启动 parsing
        created_by=admin.id,
    )
    db.add(doc)
    await db.commit()       # 必须先 commit，拿到自增 id，后台任务才查得到这行
    await db.refresh(doc)   # 刷新获取 doc.id 及数据库默认值

    # ---------- 4. 将"解析 + 切片 + 向量化 + 入库"丢给后台线程 ----------
    # BackgroundTasks 会在响应发送给客户端之后、连接关闭前执行
    background_tasks.add_task(run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status}


# ---------------------------------------------------------------------------
# 分页查询知识文档列表
# ---------------------------------------------------------------------------
@router.get("", response_model=DocumentListResponse)
async def get_documents(
        page: int = 1,                      # 页码，从 1 开始
        page_size: int = 10,                # 每页条数
        doc_type: str | None = None,        # 可选过滤：文档类型
        product_line: str | None = None,    # 可选过滤：产品线
        status: str | None = None,          # 可选过滤：入库状态
        db: AsyncSession = Depends(get_db),
        user: User = Depends(require_admin)
):
    """管理员视角分页查询文档列表。

    共执行 2 条 SQL：
    1) SELECT COUNT(*)  -- 用于分页器计算总页数
    2) SELECT ... JOIN sys_user ORDER BY created_at DESC LIMIT ?, ?  -- 当前页数据
    """
    # ---------- 1) 动态拼装过滤条件（count 和列表查询共用一份，避免条件漂移） ----------
    conds = []
    if doc_type is not None:
        conds.append(KgDocument.doc_type == doc_type)
    if product_line is not None:
        conds.append(KgDocument.product_line == product_line)
    if status is not None:
        conds.append(KgDocument.status == status)
    # 【可扩展】若后续业务要求"普通工程师只能看自己上传的"，取消注释下一行：
    # conds.append(KgDocument.created_by == user.id)

    # ---------- 2) 查总数（基于未分页的过滤结果） ----------
    total = await db.scalar(select(func.count(KgDocument.id)).where(*conds)) or 0

    # ---------- 3) 查当前页列表 ----------
    # 必须 JOIN sys_user 拿上传人姓名；
    # 双字段排序 (created_at DESC, id DESC) 保证"同一秒创建的多条"顺序稳定可预期；
    # SQLAlchemy offset/limit 对应 MySQL 的 LIMIT offset, row_count。
    stmt = (
        select(KgDocument, User.display_name.label("created_by_name"))
        .join(User, KgDocument.created_by == User.id)
        .where(*conds)
        .order_by(KgDocument.created_at.desc(), KgDocument.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    # db.execute() 返回的行是 (KgDocument 实例, created_by_name) 元组，
    # 不能用 db.scalars()（scalars 只取每行第一列），否则会丢失上传人姓名
    items = [DocumentItem(**_document_payload(row[0], row.created_by_name))
             for row in (await db.execute(stmt)).all()]
    return DocumentListResponse(total=total, items=items)

# ---------------------------------------------------------------------------
# 文档详情（附带 file_type、updated_at 两个列表页不需要的字段）
# ---------------------------------------------------------------------------
@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(doc_id: int, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_admin)):
    """查询单篇文档详情，供前端详情抽屉展示。"""
    row = (await db.execute(
        select(KgDocument, User.display_name.label("created_by_name"))
        .join(User, KgDocument.created_by == User.id)
        .where(KgDocument.id == doc_id)
    )).first()
    if row is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc, created_by_name = row
    # 详情接口比列表多返回 file_type（原始文件扩展名）和 updated_at（最后修改时间）
    return DocumentDetail(**_document_payload(doc, created_by_name),
                          file_type=doc.file_type, updated_at=doc.updated_at)


# ---------------------------------------------------------------------------
# 删除文档（向量库 + MySQL chunk + MySQL document 行 + 本地文件 四处联动清理）
# ---------------------------------------------------------------------------
@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db),
                    admin: User = Depends(require_admin)):
    """彻底删除文档。

    为避免删除"正在写入的中间状态"数据，parsing 状态下拒绝删除，前端需禁用对应按钮。
    """
    doc = await db.get(KgDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    # parsing 状态下后台任务可能在写 Milvus / MySQL，强行删除会导致脏数据
    if doc.status == "parsing":
        raise HTTPException(status_code=409, detail="文档正在入库中，请稍后再删除")

    # ingest_service 内部负责 4 处联动清理：Milvus 向量 + KgDocumentChunk 行 +
    # KgDocument 行 + 本地原始文件；任何一步失败都在同一事务内回滚
    await ingest_service.delete_document_everywhere(db, doc)
    return {"doc_id": doc_id, "deleted": True}


# ---------------------------------------------------------------------------
# 重新上传新版本（同一条 kg_document 记录，version 自增，旧 chunk 与旧文件清理后重走流水线）
# ---------------------------------------------------------------------------
@router.post("/{doc_id}/reingest")
async def reingest_document(
    doc_id: int,                             # 目标文档 ID（沿用旧记录，不新增行）
    background_tasks: BackgroundTasks,       # 后台任务：重跑入库流水线
    file: UploadFile,                        # 新文件体
    product_version: str = Form(...),        # 通常随新版本号一起改
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """重新上传文档新版。

    与 upload 的核心区别：
    - 不新增 KgDocument 记录，在原行上更新字段 + version + 1
    - 先清理旧 chunk 的 Milvus + MySQL 数据（_purge_chunks），避免新旧版本向量混用
    - 删除本地旧文件（新文件已用新 uuid 存了新路径）

    Args:
        doc_id: 目标文档主键
        product_version: 新的产品版本号（表单字段，前端要求每次重传显式填写）
    """
    doc = await db.get(KgDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 同样禁止在 parsing 状态下重传，否则后台旧流水线 + 新流水线同时操作同一 doc 会乱
    if doc.status == "parsing":
        raise HTTPException(status_code=409, detail="文档正在入库中，请稍后再操作")

    # ---- 三步核心操作：新文件保存 -> 旧 chunk 清理 -> 记录字段更新 ----
    # 1) 新文件落盘（走与 upload 完全相同的 uuid 命名逻辑，不会覆盖旧路径）
    new_path, new_file_size, new_ext = _save_upload(file)
    # 2) 清理旧 chunk 两处数据（Milvus + MySQL chunk 行），保留 kg_document 这一行
    await _purge_chunks(db, doc)
    # 3) 删掉本地旧文件（旧路径已经不再被任何记录引用，避免 uploads/ 目录无限膨胀）
    old_abs = os.path.join(settings.BASE_DIR, doc.file_path)
    if os.path.exists(old_abs):
        os.remove(old_abs)

    # ---- 更新 kg_document 行字段 ----
    doc.file_path, doc.file_type = new_path, new_ext
    doc.file_size = new_file_size       # 新文件大小（字节）
    doc.product_version = product_version
    doc.version += 1                    # 语义版本自增，前端表格直接展示
    doc.status = "pending"              # 重置为 pending，等待新流水线启动
    doc.chunk_count = 0                 # 旧 chunk 已清，计数归零
    await db.commit()

    # ---- 后台异步重新执行入库流水线 ----
    background_tasks.add_task(run_ingest_pipeline, doc.id)
    return {"doc_id": doc.id, "status": doc.status, "version": doc.version}
