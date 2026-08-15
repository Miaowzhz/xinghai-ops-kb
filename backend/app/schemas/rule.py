# backend/app/schemas/rule.py
from typing import Literal
from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    rule_name: str = Field(min_length=1, max_length=64)
    rule_type: Literal["sensitive_op", "high_risk_cmd", "price"]
    action: Literal["block", "confirm"]
    match_type: Literal["keyword", "regex"]
    pattern: str = Field(min_length=1, max_length=512)
    reply_text: str = Field(min_length=1)
    enabled: bool = True


class RuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_type: Literal["sensitive_op", "high_risk_cmd", "price"] | None = None
    action: Literal["block", "confirm"] | None = None
    match_type: Literal["keyword", "regex"] | None = None
    pattern: str | None = None
    reply_text: str | None = None
    enabled: bool | None = None      # 用于"启停规则"，不必删除


class RuleOut(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    action: str
    match_type: str
    pattern: str
    reply_text: str
    enabled: bool