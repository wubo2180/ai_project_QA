"""用户认证 API。"""
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """用户注册。"""
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()
    password2 = request.data.get("password2", "").strip()

    if not username or not password:
        return Response({"error": "用户名和密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

    if len(username) < 2:
        return Response({"error": "用户名至少 2 个字符"}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({"error": "密码至少 6 个字符"}, status=status.HTTP_400_BAD_REQUEST)

    if password != password2:
        return Response({"error": "两次密码不一致"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    # 注册后自动登录
    login(request, user)
    return Response({
        "user": {"id": user.id, "username": user.username},
        "message": "注册成功",
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    """用户登录。"""
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()

    if not username or not password:
        return Response({"error": "用户名和密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)

    login(request, user)
    return Response({
        "user": {"id": user.id, "username": user.username},
        "message": "登录成功",
    })


@api_view(["POST"])
def user_logout(request):
    """用户退出登录。"""
    logout(request)
    return Response({"message": "已退出登录"})


@api_view(["GET"])
def current_user(request):
    """获取当前登录用户信息。"""
    if not request.user.is_authenticated:
        return Response({"user": None}, status=status.HTTP_200_OK)
    return Response({
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "date_joined": request.user.date_joined.isoformat(),
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """获取 CSRF Token。"""
    return Response({"csrfToken": get_token(request)})
