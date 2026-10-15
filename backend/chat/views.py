"""聊天 API 视图。"""
import json
import logging

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .dify_api import DifyClient
from .excel_export import extract_tables, tables_to_excel
from .web_search import web_search, format_search_context

logger = logging.getLogger(__name__)


@api_view(["POST"])
def chat_message(request):
    """处理用户消息，调用 LLM 返回回复。"""
    user_message = request.data.get("message", "").strip()
    conversation_id = request.data.get("conversation_id") or None

    if not user_message:
        return Response(
            {"error": "消息不能为空"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = DifyClient()
        reply, conv_id = client.chat(
            user_message,
            user=str(getattr(request.user, "id", "web-user") or "web-user"),
            conversation_id=conversation_id,
        )

        return Response({
            "reply": reply,
            "conversation_id": conv_id,
            "status": "success",
        })

    except Exception as e:
        logger.exception("Dify 调用异常")
        return Response(
            {
                "error": f"服务暂时不可用，请稍后重试",
                "detail": str(e) if settings.DEBUG else "",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["POST"])
def export_excel(request):
    """将回复中的 Markdown 表格导出为 Excel 文件。"""
    content = request.data.get("content", "")
    filename = request.data.get("filename", "导出数据")

    if not content:
        return Response(
            {"error": "内容不能为空"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tables = extract_tables(content)
    if not tables:
        return Response(
            {"error": "未检测到表格数据"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        excel_buffer = tables_to_excel(tables)
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        safe_filename = filename.replace("/", "_").replace("\\", "_")[:100]
        response["Content-Disposition"] = f'attachment; filename="{safe_filename}.xlsx"'
        return response

    except Exception as e:
        logger.exception("Excel 导出异常")
        return Response(
            {"error": f"导出失败: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def health_check(request):
    """健康检查接口。"""
    llm_configured = bool(settings.DIFY_API_KEY)
    return Response({
        "status": "ok",
        "llm_configured": llm_configured,
    })


def chat_stream(request):
    """流式聊天 SSE 端点。"""
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    user_message = body.get("message", "").strip()
    web_search_enabled = body.get("web_search", False)
    conversation_id = body.get("conversation_id") or None
    user_id = str(getattr(request.user, "id", None) or "web-user")

    if not user_message:
        return HttpResponse(status=400)

    def event_stream():
        query = user_message

        # 如果开启网页搜索，先搜索并把结果拼接到用户问题中
        if web_search_enabled:
            yield f"data: {json.dumps({'type': 'status', 'content': '正在搜索网页...'})}\n\n".encode("utf-8")
            search_results = web_search(user_message)
            if search_results:
                search_context = format_search_context(user_message, search_results)
                query = f"{search_context}\n\n用户问题：{user_message}"
                yield f"data: {json.dumps({'type': 'status', 'content': f'已获取 {len(search_results)} 条搜索结果'})}\n\n".encode("utf-8")

        try:
            client = DifyClient()
            full_content = ""
            for event in client.chat_stream(query, user=user_id, conversation_id=conversation_id):
                etype = event.get("type")
                if etype == "chunk":
                    full_content += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']})}\n\n".encode("utf-8")
                elif etype == "conversation":
                    yield f"data: {json.dumps({'type': 'conversation', 'conversation_id': event['conversation_id']})}\n\n".encode("utf-8")
                elif etype == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': event['content']})}\n\n".encode("utf-8")
                    return

            yield f"data: {json.dumps({'type': 'done', 'content': full_content})}\n\n".encode("utf-8")

        except Exception as e:
            logger.exception("Dify 流式调用异常")
            error_msg = str(e) if settings.DEBUG else "服务暂时不可用，请稍后重试"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n".encode("utf-8")

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
