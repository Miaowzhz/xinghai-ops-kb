# backend/app/agent/graph.py
from functools import partial
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent import nodes


def route_after_intent(state: AgentState) -> str:
    # intent_recognition 判定为闲聊/无关问题时已写入固定话术，直接走 respond 输出，
    # 不检索、不调护栏；只有 ops_qa 才进入 guardrail_check
    return "respond" if state.get("intent") in ("chitchat", "faq") else "guardrail"


def route_after_guardrail(state: AgentState) -> str:
    # guardrail_check 命中 block 规则时已写入 status=blocked，直接结束
    return "blocked" if state.get("status") == "blocked" else "continue"


def route_after_fuse(state: AgentState) -> str:
    # fuse_rerank 判定无可靠依据时 fused_chunks 为空，走 refuse 拒答节点
    return "refuse" if not state.get("fused_chunks") else "generate"


def route_after_verify(state: AgentState) -> str:
    # 引用校验失败且未重试过：回到 generate 重新生成（最多 1 次）
    if state.get("status") == "verify_failed" and state.get("retry_count", 0) < 1:
        return "regenerate"
    return "respond"


def build_graph(db):
    """每次请求调用：把当前请求的 db session 用 partial 绑进需要它的节点，再编译。

    需要 db 的节点：guardrail_check（查 guardrail_rule）、hybrid_retrieve（回源 MySQL）。
    节点函数签名为 (state, db)，LangGraph 调用时只传 state，db 在这里预先绑定。
    模块级 qa_graph = builder.compile() 单例仅适用于无 db 依赖的简化形态，
    接入 db 节点后统一用本工厂做请求级构建（与 T03 §2.4 一致）。
    """
    builder = StateGraph(AgentState)

    builder.add_node("intent_recognition", nodes.intent_recognition)
    builder.add_node("guardrail_check", partial(nodes.guardrail_check, db=db))
    builder.add_node("decompose", nodes.decompose)
    builder.add_node("hybrid_retrieve", partial(nodes.hybrid_retrieve, db=db))
    builder.add_node("fuse_rerank", nodes.fuse_rerank)
    builder.add_node("refuse", nodes.refuse)
    builder.add_node("generate", nodes.generate)
    builder.add_node("citation_verify", nodes.citation_verify)
    builder.add_node("respond", nodes.respond)

    builder.set_entry_point("intent_recognition")
    builder.add_conditional_edges(
        "intent_recognition", route_after_intent,
        {"respond": "respond", "guardrail": "guardrail_check"},  # chitchat/faq 直接出固定话术
    )
    builder.add_conditional_edges(
        "guardrail_check", route_after_guardrail,
        {"blocked": "respond", "continue": "decompose"},  # 拦截也要走 respond 落库+推送
    )
    builder.add_edge("decompose", "hybrid_retrieve")
    builder.add_edge("hybrid_retrieve", "fuse_rerank")
    builder.add_conditional_edges(
        "fuse_rerank", route_after_fuse,
        {"refuse": "refuse", "generate": "generate"},
    )
    builder.add_edge("refuse", "respond")
    builder.add_edge("generate", "citation_verify")
    builder.add_conditional_edges(
        "citation_verify", route_after_verify,
        {"regenerate": "generate", "respond": "respond"},
    )
    builder.add_edge("respond", END)

    return builder.compile()