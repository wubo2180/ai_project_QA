from django.urls import path, re_path

from . import views
from . import views_history
from . import views_auth

urlpatterns = [
    # 聊天
    path("chat/", views.chat_message, name="chat"),
    re_path(r"^chat-stream/$", views.chat_stream, name="chat-stream"),
    path("export-excel/", views.export_excel, name="export-excel"),
    path("health/", views.health_check, name="health"),
    # 对话历史
    path("conversations/", views_history.conversation_list, name="conv-list"),
    path("conversations/<uuid:pk>/", views_history.conversation_detail, name="conv-detail"),
    path("conversations/<uuid:conv_pk>/messages/", views_history.add_message, name="conv-message"),
    # 用户认证
    path("auth/register/", views_auth.register, name="register"),
    path("auth/login/", views_auth.user_login, name="login"),
    path("auth/logout/", views_auth.user_logout, name="logout"),
    path("auth/me/", views_auth.current_user, name="current-user"),
    path("auth/csrf/", views_auth.get_csrf_token, name="csrf"),
    # 模型
    path("models/", views.available_models, name="available-models"),
]
