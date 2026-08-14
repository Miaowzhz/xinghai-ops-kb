# backend/app/schemas/qa.py
from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str | None = None  # 不传则由后端用首条问题生成


class SessionOut(BaseModel):
    id: int
    title: str
    message_count: int = 0      # 会话内消息数，COUNT(qa_message) 派生，P06 列表展示用；新建会话为 0
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: list[dict] | None = None
    status: str
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: int | None = None       # 不传则新建会话
    question: str = Field(min_length=1, max_length=2000)
    product_line: str | None = None     # 可选：产品线过滤，如 ECS / VPC / RDS
    product_version: str | None = None  # 可选：版本过滤，如 V3.2