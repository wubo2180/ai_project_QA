"""聊天 API 视图。"""
import json
import logging

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .llm_api import LLMClient
from .excel_export import extract_tables, tables_to_excel
from .web_search import web_search, format_search_context

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
    return Response({
        "status": "ok",
        "llm_configured": bool(settings.LLM_API_KEY),
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
    history = body.get("history", [])
    web_search_enabled = body.get("web_search", False)
    model_provider = body.get("model", "deepseek")  # 默认 deepseek
    image_data = body.get("image_data", None)  # base64 图片（仅 qwen 支持）

    if not user_message:
        return HttpResponse(status=400)

    def event_stream():
        messages = list(history)

        # 如果开启网页搜索，先搜索并注入上下文
        if web_search_enabled:
            yield f"data: {json.dumps({'type': 'status', 'content': '正在搜索网页...'})}\n\n".encode("utf-8")
            search_results = web_search(user_message)
            if search_results:
                search_context = format_search_context(user_message, search_results)
                messages.append({"role": "system", "content": search_context})
                yield f"data: {json.dumps({'type': 'status', 'content': f'已获取 {len(search_results)} 条搜索结果'})}\n\n".encode("utf-8")

        # 构建用户消息（支持图片多模态）
        if image_data:
            user_msg = {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                ],
            }
        else:
            user_msg = {"role": "user", "content": user_message}
        messages.append(user_msg)

        try:
            client = LLMClient(provider=model_provider)
            full_content = ""
            for chunk in client.chat_stream(messages):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n".encode("utf-8")

            yield f"data: {json.dumps({'type': 'done', 'content': full_content})}\n\n".encode("utf-8")

        except Exception as e:
            logger.exception("LLM 流式调用异常")
            error_msg = str(e) if settings.DEBUG else "服务暂时不可用，请稍后重试"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n".encode("utf-8")

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
def available_models(request):
    """获取可用的模型列表（不含敏感字段）。"""
    models = {}
    for key, cfg in settings.AVAILABLE_MODELS.items():
        models[key] = {
            "label": cfg["label"],
            "model": cfg["model"],
            "supports_image": cfg["supports_image"],
        }
    return Response(models)
