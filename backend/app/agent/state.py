# backend/app/agent/state.py
from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str                 # 用户原始问题
    session_id: int               # 会话 ID（respond 节点落库用）
    history: list[dict]           # 最近 10 条历史消息 [{"role", "content"}]
    product_line: str | None      # 检索过滤条件
    product_version: str | None
    intent: str                   # intent_recognition 输出：faq / ops_qa / chitchat
    sub_questions: list[str]      # decompose 输出：子问题列表（简单问题为 [原问题]）
    retrieved_chunks: list[dict]  # hybrid_retrieve 输出：各子问题召回的 chunk 合集
    fused_chunks: list[dict]      # fuse_rerank 输出：融合重排后的 top5
    answer: str                   # generate 输出：带 [1][2] 引用编号的答案
    citations: list[dict]         # citation_verify 输出：校验通过的引用列表
    status: str                   # 最终消息状态：normal / blocked / refused / failed
    guardrail_rule_id: int        # guardrail_check 命中 block 规则时写入，落库 qa_message.guardrail_rule_id
    retry_count: int              # citation_verify 失败后的重试次数（上限 1）