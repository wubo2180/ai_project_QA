from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "excel_mode", "created_at"]


class ConversationListSerializer(serializers.ModelSerializer):
    """对话列表（含消息数量）。"""
    message_count = serializers.SerializerMethodField()
    last_content = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "message_count", "last_content", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_content(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return last.content[:100] if last else ""


class ConversationDetailSerializer(serializers.ModelSerializer):
    """对话详情（含所有消息）。"""
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "messages", "created_at", "updated_at"]


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["title"]
