# backend/app/core/sse.py
import json


def sse_event(event_type: str, payload: dict) -> str:
    """按 SSE 协议格式化一条事件：data: {...}\\n\\n"""
    return f"data: {json.dumps({'type': event_type, **payload}, ensure_ascii=False)}\n\n"