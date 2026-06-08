"""对话历史 CRUD API。"""
import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
def conversation_list(request):
    """获取对话列表 / 创建新对话。"""
    if request.method == "GET":
        qs = Conversation.objects.all()
        serializer = ConversationListSerializer(qs, many=True)
        return Response(serializer.data)

    # POST - 创建新对话
    serializer = ConversationCreateSerializer(data=request.data)
    if serializer.is_valid():
        conv = serializer.save()
        return Response(
            ConversationDetailSerializer(conv).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE", "PATCH"])
def conversation_detail(request, pk):
    """获取/删除/修改对话。"""
    try:
        conv = Conversation.objects.get(pk=pk)
    except Conversation.DoesNotExist:
        return Response({"error": "对话不存在"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ConversationDetailSerializer(conv).data)

    if request.method == "DELETE":
        conv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH - 更新标题
    title = request.data.get("title")
    if title:
        conv.title = title
        conv.save()
        return Response(ConversationListSerializer(conv).data)
    return Response({"error": "缺少 title"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def add_message(request, conv_pk):
    """向对话中添加消息。"""
    try:
        conv = Conversation.objects.get(pk=conv_pk)
    except Conversation.DoesNotExist:
        return Response({"error": "对话不存在"}, status=status.HTTP_404_NOT_FOUND)

    serializer = MessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    msg = serializer.save(conversation=conv)

    # 自动更新对话标题（第一条用户消息）
    if msg.role == "user" and conv.title == "新对话":
        conv.title = msg.content[:30] + ("..." if len(msg.content) > 30 else "")
        conv.save()

    return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
