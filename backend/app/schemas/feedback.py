# backend/app/schemas/feedback_service.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message_id: int
    feedback_type: Literal["like", "dislike"]
    reason: str | None = Field(default=None, max_length=500)  # dislike 时必填（service 校验）


class FeedbackOut(BaseModel):
    id: int
    message_id: int
    feedback_type: str
    reason: str | None
    status: str


class AuditTaskOut(BaseModel):
    id: int
    feedback_id: int
    message_id: int
    status: str
    resolution: str | None
    resolved_by: int | None
    resolved_at: datetime | None
    created_at: datetime


class AuditTaskDetail(AuditTaskOut):
    question: str                    # 当时的用户问题（qa_message role=user）
    answer: str                      # 当时的答案原文
    message_status: str              # normal / blocked / refused / failed
    citations: list[dict] | None     # 引用快照 JSON（文档已删也能展示）
    dislike_reason: str | None       # 点踩原因
    document_deleted: bool           # 关联文档是否已被删除（前端提示用）


class ResolveRequest(BaseModel):
    status: Literal["resolved", "rejected"]
    resolution: str = Field(min_length=1, max_length=1000)  # 结论必填