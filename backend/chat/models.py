import uuid
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """对话记录。"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversations",
        verbose_name="所属用户",
    )
    title = models.CharField("对话标题", max_length=255, default="新对话")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"[{self.created_at:%m-%d %H:%M}] {self.title}"


class Message(models.Model):
    """单条消息。"""
    ROLE_CHOICES = [
        ("user", "用户"),
        ("assistant", "AI"),
        ("system", "系统"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField("角色", max_length=16, choices=ROLE_CHOICES)
    content = models.TextField("内容")
    excel_mode = models.BooleanField("Excel 模式", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}..."
