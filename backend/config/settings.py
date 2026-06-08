import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-dev-key-change-in-production"

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("DB_NAME", "ai_project_qa"),
        "USER": os.getenv("DB_USER", "ai_project_QA"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "172.20.46.18"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "chat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "config.urls"

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "chat.auth_patch.NoCSRFSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

STATIC_URL = "static/"

# LLM 配置 — DeepSeek
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# LLM 配置 — Qwen（通义千问）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_URL = os.getenv("QWEN_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-vl-max")

# 可用模型列表（供前端下拉选择）
AVAILABLE_MODELS = {
    "deepseek": {
        "label": "DeepSeek",
        "api_key": LLM_API_KEY,
        "api_url": LLM_API_URL,
        "model": LLM_MODEL,
        "supports_image": False,
    },
    "qwen": {
        "label": "通义千问 (Qwen)",
        "api_key": QWEN_API_KEY,
        "api_url": QWEN_API_URL,
        "model": QWEN_MODEL,
        "supports_image": True,
    },
}
