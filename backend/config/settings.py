import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件（显式指定绝对路径，避免工作目录不同导致读取不到）
load_dotenv(BASE_DIR / ".env")

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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.openai.com/v1/chat/completions")
DEEPSEEK_FLASH_MODEL = os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash")
DEEPSEEK_PRO_MODEL = os.getenv("DEEPSEEK_PRO_MODEL", "deepseek-v4-pro")
# LLM 配置 — Qwen（通义千问）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_API_URL = os.getenv("QWEN_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
QWEN_PLUS_MODEL = os.getenv("QWEN_PLUS_MODEL", "qwen3.7-plus")
QWEN_MAX_MODEL = os.getenv("QWEN_MAX_MODEL", "qwen3.7-max")

# LLM 配置 — GPT
GPT_API_URL = os.getenv("GPT_API_URL", "https://api.lmuai.com/v1")
GPT_API_KEY = os.getenv("GPT_API_KEY", "")
GPT_5_5_MODEL = os.getenv("GPT_5_5_MODEL", "gpt-5.5")

# 可用模型列表（供前端下拉选择）
AVAILABLE_MODELS = {
    "deepseek_flash": {
        "label": "DeepSeek_Flash",
        "api_key": DEEPSEEK_API_KEY,
        "api_url": DEEPSEEK_API_URL,
        "model": DEEPSEEK_FLASH_MODEL,
        "supports_image": False,
    },
    "deepseek_pro": {
        "label": "DeepSeek_Pro",
        "api_key": DEEPSEEK_API_KEY,
        "api_url": DEEPSEEK_API_URL,
        "model": DEEPSEEK_PRO_MODEL,
        "supports_image": False,
        
    },
    "qwen_plus": {
        "label": "Qwen_Plus",
        "api_key": QWEN_API_KEY,
        "api_url": QWEN_API_URL,
        "model": QWEN_PLUS_MODEL,
        "supports_image": True,
    },
        "qwen_max": {
        "label": "Qwen_Max",
        "api_key": QWEN_API_KEY,
        "api_url": QWEN_API_URL,
        "model": QWEN_MAX_MODEL,
        "supports_image": True,
    },
        "gpt": {
        "label": "GPT",
        "api_key": GPT_API_KEY,
        "api_url": GPT_API_URL,
        "model": GPT_5_5_MODEL,
        "supports_image": True,
    }
}
