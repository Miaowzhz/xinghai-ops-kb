# backend/app/agent/nodes.py
from langchain_openai import ChatOpenAI
from app.config import settings
from app.services import retrieval_service, guardrail_service  # guardrail: Stage 5
from app.agent.prompts import INTENT_PROMPT, DECOMPOSE_PROMPT, GENERATE_PROMPT
from app.agent.state import AgentState

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1,
)


CHITCHAT_REPLY = "您好，我是星海运维智能知识库助手，可以为您解答云产品运维相关问题。"
FAQ_REPLY = "该问题超出运维知识库的服务范围，请描述具体的云产品运维问题。"


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


async def guardrail_check(state: AgentState, db) -> dict:
    # 命中 action=block 的规则：直接给出拦截话术，状态置 blocked，不再检索/生成
    rule = await guardrail_service.match_block_rule(db, state["question"])
    if rule:
        return {
            "answer": rule.reply_text,
            "citations": [],
            "status": "blocked",
            "guardrail_rule_id": rule.id,  # 命中规则 id 落库 qa_message.guardrail_rule_id（审计用）
        }
    return {}


async def decompose(state: AgentState) -> dict:
    prompt = DECOMPOSE_PROMPT.format(history=state["history"], question=state["question"])
    resp = await llm.ainvoke(prompt)
    subs = [line.strip() for line in resp.content.splitlines() if line.strip()]
    return {"sub_questions": subs or [state["question"]]}


async def hybrid_retrieve(state: AgentState, db) -> dict:
    chunks = []
    for q in state.get("sub_questions") or [state["question"]]:
        chunks += await retrieval_service.hybrid_retrieve(
            db, q, state.get("product_line"), state.get("product_version")
        )
    # 按 chunk_id 去重（同一 chunk 可能被多个子问题召回）
    dedup = {c["chunk_id"]: c for c in chunks}
    return {"retrieved_chunks": list(dedup.values())}


async def fuse_rerank(state: AgentState) -> dict:
    """融合重排取 top5；无可用片段时只写空列表，由条件边路由到 refuse 节点。"""
    chunks = sorted(state["retrieved_chunks"], key=lambda c: c["score"], reverse=True)[:5]
    if not chunks or chunks[0]["score"] < retrieval_service.MIN_RRF_SCORE:
        return {"fused_chunks": []}
    return {"fused_chunks": chunks}


async def refuse(state: AgentState) -> dict:
    """拒答节点：检索不到可靠依据，明确告知而不是让大模型编造。"""
    return {
        "answer": "当前知识库未找到可靠依据，建议联系值班专家或补充相关文档。",
        "citations": [],
        "status": "refused",
    }


async def generate(state: AgentState) -> dict:
    context = "\n\n".join(
        f"[{i}]（{c['document_title']} {c['product_version']}）{c['snippet']}"
        for i, c in enumerate(state["fused_chunks"], start=1)
    )
    prompt = GENERATE_PROMPT.format(
        context=context, history=state["history"], question=state["question"]
    )
    resp = await llm.ainvoke(prompt)
    return {"answer": resp.content}