# backend/app/routers/qa.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.schemas.qa import SessionCreate, SessionOut, MessageOut
from app.services import qa_service
from fastapi.responses import StreamingResponse
from app.core.sse import sse_event
from app.agent.graph import build_graph
from app.schemas.qa import ChatRequest



router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/sessions", response_model=SessionOut)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await qa_service.create_session(db, user.id, body.title or "新会话")


@router.get("/sessions", response_model=list[SessionOut])
async def get_sessions(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await qa_service.list_sessions(db, user.id)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await qa_service.list_messages(db, session_id, user.id)



@router.post("/chat")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1. 复用或新建会话
    if body.session_id:
        await qa_service.check_owner(db, body.session_id, user.id)
        session_id = body.session_id
    else:
        session = await qa_service.create_session(db, user.id, title=body.question[:50])
        session_id = session.id

    # 2. 落库用户消息（role=user），保留 id 作为 assistant 消息的 reply_to_id
    user_msg = await qa_service.save_message(db, session_id, role="user", content=body.question)

    # 3. 读最近 10 条历史，组装初始 state
    history = await qa_service.load_history(db, session_id)
    init_state = {
        "question": body.question,
        "session_id": session_id,
        "history": history,
        "product_line": body.product_line,
        "product_version": body.product_version,
        "retry_count": 0,
    }

    async def event_stream():
        try:
            graph = build_graph(db)                  # 请求级构建：把当前请求的 db session 绑进节点
            final = await graph.ainvoke(init_state)  # 执行 LangGraph 工作流
            # respond 逻辑：先推答案，再推引用，最后落库
            for chunk in _split_answer(final["answer"]):  # 按小片段模拟逐字推送
                yield sse_event("token", {"content": chunk})
            if final.get("citations"):
                yield sse_event("citations", {"items": final["citations"]})
            if final.get("status") != "normal":
                yield sse_event("status", {"status": final["status"]})
            await qa_service.save_message(
                db, session_id, role="assistant", content=final["answer"],
                status=final.get("status", "normal"), citations=final.get("citations"),
                guardrail_rule_id=final.get("guardrail_rule_id"),  # 护栏命中时由 guardrail_check 写入 state
                reply_to_id=user_msg.id,                           # 问答对显式关联，M05 审核详情按它取原始问题
            )
            yield sse_event("done", {"session_id": session_id})
        except Exception:
            # 大模型超时/限流等：发 error 事件 + 写 failed 占位消息，连接正常关闭
            await qa_service.save_message(
                db, session_id, role="assistant",
                content="系统繁忙，请稍后重试。", status="failed",
                reply_to_id=user_msg.id,
            )
            yield sse_event("error", {"message": "系统繁忙，请稍后重试。"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")