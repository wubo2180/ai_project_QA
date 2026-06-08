"""聊天 API 视图。"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .llm_api import LLMClient

logger = logging.getLogger(__name__)


@api_view(["POST"])
def chat_message(request):
    """处理用户消息，调用 LLM 返回回复。"""
    user_message = request.data.get("message", "").strip()
    history = request.data.get("history", [])

    if not user_message:
        return Response(
            {"error": "消息不能为空"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 构建消息历史
    messages = list(history)
    messages.append({"role": "user", "content": user_message})

    try:
        client = LLMClient()
        reply = client.chat(messages)

        return Response({
            "reply": reply,
            "status": "success",
        })

    except Exception as e:
        logger.exception("LLM 调用异常")
        return Response(
            {
                "error": f"服务暂时不可用，请稍后重试",
                "detail": str(e) if settings.DEBUG else "",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
def health_check(request):
    """健康检查接口。"""
    return Response({
        "status": "ok",
        "llm_configured": bool(settings.LLM_API_KEY),
    })
