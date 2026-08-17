# backend/app/agent/nodes.py
from langchain_openai import ChatOpenAI
from app.config import settings
from app.services import retrieval_service, guardrail_service  # guardrail: Stage 5
from app.agent.prompts import INTENT_PROMPT, DECOMPOSE_PROMPT, GENERATE_PROMPT
from app.agent.state import AgentState
import re

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,
)

CITATION_PATTERN = re.compile(r"\[(\d+)\]")
CHITCHAT_REPLY = "您好，我是星海运维智能知识库助手，可以为您解答云产品运维相关问题。"
FAQ_REPLY = "该问题超出运维知识库的服务范围，请描述具体的云产品运维问题。"

# 意图识别节点
async def intent_recognition(state: AgentState) -> dict:
    prompt = INTENT_PROMPT.format(history=state["history"], question=state["question"])
    resp = await llm.ainvoke(prompt)
    intent = resp.content.strip()
    if intent not in ("ops_qa", "chitchat", "faq"):
        intent = "ops_qa"  # 模型输出不听话时按运维问答处理，走最完整链路
    if intent == "chitchat":
        # 闲聊/无关问题：直接给固定话术，由条件边跳到 respond，不检索、不调护栏
        return {"intent": intent, "answer": CHITCHAT_REPLY, "citations": [], "status": "normal"}
    if intent == "faq":
        return {"intent": intent, "answer": FAQ_REPLY, "citations": [], "status": "normal"}
    return {"intent": intent}

# 护栏检查节点
async def guardrail_check(state: AgentState, db) -> dict:
    """护栏校验：命中 block 规则直接出拦截话术；命中 confirm 规则记录提示语。"""
    question = state["question"]

    # 1. block 规则：不做检索、不调生成，直接结束（业务流程规则：护栏优先于一切）
    block_rule = await guardrail_service.match_block_rule(db, question)
    if block_rule:
        return {
            "answer": block_rule.reply_text,
            "citations": [],
            "status": "blocked",
            "guardrail_rule_id": block_rule.id,  # 命中规则 id 写入 state，由 respond 落库 qa_message.guardrail_rule_id
        }

    # 2. confirm 规则：不拦截，把提示语写进 state，generate 节点拼到提示词里
    confirm_rules = await guardrail_service.match_confirm_rules(db, question)
    if confirm_rules:
        notices = "；".join(r.reply_text for r in confirm_rules)
        return {"confirm_notice": notices}
    return {}


# 问题分解节点
async def decompose(state: AgentState) -> dict:
    prompt = DECOMPOSE_PROMPT.format(history=state["history"], question=state["question"])
    resp = await llm.ainvoke(prompt)
    subs = [line.strip() for line in resp.content.splitlines() if line.strip()]
    return {"sub_questions": subs or [state["question"]]}


# 混合检索节点
async def hybrid_retrieve(state: AgentState, db) -> dict:
    chunks = []
    for q in state.get("sub_questions") or [state["question"]]:
        chunks += await retrieval_service.hybrid_retrieve(
            db, q, state.get("product_line"), state.get("product_version")
        )
    # 按 chunk_id 去重（同一 chunk 可能被多个子问题召回）
    dedup = {c["chunk_id"]: c for c in chunks}
    return {"retrieved_chunks": list(dedup.values())}


# 融合重排节点
async def fuse_rerank(state: AgentState) -> dict:
    """融合重排取 top5；无可用片段时只写空列表，由条件边路由到 refuse 节点。"""
    chunks = sorted(state["retrieved_chunks"], key=lambda c: c["score"], reverse=True)[:5]
    if not chunks or chunks[0]["score"] < retrieval_service.MIN_RRF_SCORE:
        return {"fused_chunks": []}
    return {"fused_chunks": chunks}


# 拒答节点
async def refuse(state: AgentState) -> dict:
    """拒答节点：检索不到可靠依据，明确告知而不是让大模型编造。"""
    return {
        "answer": "当前知识库未找到可靠依据，建议联系值班专家或补充相关文档。",
        "citations": [],
        "status": "refused",
    }


# 生成答案节点
async def generate(state: AgentState) -> dict:
    context = "\n\n".join(
        f"[{i}]（{c['document_title']} {c['product_version']}）{c['snippet']}"
        for i, c in enumerate(state["fused_chunks"], start=1)
    )
    prompt = GENERATE_PROMPT.format(
        context=context,
        history=state["history"],
        question=state["question"],
        confirm_notice=state.get("confirm_notice", "无"),
    )
    resp = await llm.ainvoke(prompt)
    return {"answer": resp.content}


async def citation_verify(state: AgentState) -> dict:
    """校验答案中的引用编号 [n] 是否都真实存在于 fused_chunks。"""
    chunks = state.get("fused_chunks", [])
    answer = state.get("answer", "")
    cited_indexes = {int(n) for n in CITATION_PATTERN.findall(answer)}

    # 规则一：答案一个引用都没有 → 视为失败（无来源的结论不允许输出）
    # 规则二：引用了不存在的编号（如只有 5 个片段却写 [7]）→ 失败
    if not cited_indexes or any(i < 1 or i > len(chunks) for i in cited_indexes):
        retry_count = state.get("retry_count", 0)
        if retry_count < 1:
            # 回 generate 重新生成（图的条件边根据 status=verify_failed 路由）
            return {"status": "verify_failed", "retry_count": retry_count + 1}
        # 已重试 1 次仍失败 → 降级：不输出模型总结，只给片段列表和来源
        degraded = "未生成可靠总结，以下是与问题最相关的知识片段，请直接参考：\n" + "\n".join(
            f"[{i}]（{c['document_title']} {c['product_version']}）{c['snippet']}"
            for i, c in enumerate(chunks, start=1)
        )
        return {
            "answer": degraded,
            "citations": _build_citations(chunks, set(range(1, len(chunks) + 1))),
            "status": "normal",
            "retry_count": retry_count,
        }

    # 校验通过：把答案实际引用的编号映射为 citations JSON
    return {
        "citations": _build_citations(chunks, cited_indexes),
        "status": "normal",
    }


def _build_citations(chunks: list[dict], indexes: set[int]) -> list[dict]:
    """编号 n 对应 fused_chunks[n-1]，映射成前端引用卡片需要的结构。"""
    return [
        {
            "chunk_id": chunks[i - 1]["chunk_id"],
            "document_id": chunks[i - 1]["document_id"],
            "document_title": chunks[i - 1]["document_title"],
            "product_line": chunks[i - 1]["product_line"],
            "product_version": chunks[i - 1]["product_version"],
            "snippet": chunks[i - 1]["snippet"],
        }
        for i in sorted(indexes)
    ]

# 响应节点
async def respond(state: AgentState) -> dict:
    """统一补齐最终响应字段，供 SSE 和消息落库使用。"""
    status = state.get("status", "normal")
    # 引用校验重试耗尽时仍返回答案，避免前端进入未定义状态。
    if status == "verify_failed":
        status = "normal"
    return {
        "answer": state.get("answer", "系统暂时无法生成回答。"),
        "citations": state.get("citations", []),
        "status": status,
    }
