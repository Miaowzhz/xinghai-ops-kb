# backend/app/schemas/document.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

DocType = Literal["manual", "case", "sop", "api"]


class DocumentItem(BaseModel):
    id: int
    title: str
    doc_type: str
    product_line: str
    product_version: str
    status: str
    fail_reason: str | None      # status=failed 时展示失败原因（P03 列表悬浮提示）
    chunk_count: int
    version: int
    created_by_name: str         # 上传人姓名，join sys_user 取 display_name
    created_at: datetime


class DocumentDetail(DocumentItem):
    file_type: str
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentItem]