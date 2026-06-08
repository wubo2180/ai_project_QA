"""自定义认证类：Session 认证但不强制 CSRF 检查。"""
from rest_framework.authentication import SessionAuthentication


class NoCSRFSessionAuthentication(SessionAuthentication):
    """Session 认证，但跳过 CSRF 校验（前端 SPA 无需 CSRF token）。"""

    def enforce_csrf(self, request):
        pass  # 不检查 CSRF
