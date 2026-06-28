"""
对话和 RAG 查询路由模块。

提供以下 REST API 端点：
- POST /api/chat        — 非流式 RAG 对话（一次性返回完整回答）
- POST /api/chat/stream — 流式 RAG 对话（SSE 逐步推送回答）
"""

import json
import logging

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    非流式 RAG 对话。

    一次性将用户问题发送给系统，返回完整的回答和引用来源。
    如需流式输出，请使用 POST /api/chat/stream 端点。
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="流式响应请使用 POST /api/chat/stream 端点",
        )

    try:
        service = get_rag_service()
        result = service.query(
            question=request.question,
            top_k=request.top_k,
            collections=request.collections,
            history=request.history,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceReference(**s) for s in result["sources"]],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("对话查询失败")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    流式 RAG 对话（SSE 逐块推送）
    
    所有事件的 data 字段都使用 JSON 序列化：
    - sources事件：data 是 JSON 数组字符串
    - chunk事件：data 是 JSON 字符串（包含文本内容）
    - done事件：data 是空字符串的 JSON 序列化
    - error事件：data 是错误消息的 JSON 序列化
    """
    
    logger.info(f"收到流式请求: question={request.question}, collections={request.collections}")

    async def event_generator():
        """SSE 事件生成器。"""
        try:
            service = get_rag_service()
            for event in service.query_stream(
                question=request.question,
                top_k=request.top_k,
                collections=request.collections,
                history=request.history,
            ):
                # 对所有事件数据都进行 JSON 序列化
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"], ensure_ascii=False)
                }
        except Exception as e:
            logger.exception("流式查询失败")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False)
            }
            # 确保流正确结束
            yield {
                "event": "done",
                "data": json.dumps("")
            }

    return EventSourceResponse(event_generator())
