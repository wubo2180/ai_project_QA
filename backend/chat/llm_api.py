"""大模型 API 调用模块。"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """通用 LLM API 客户端，兼容 OpenAI 格式的接口。"""

    def __init__(self, provider="deepseek"):
        """初始化 LLM 客户端。
        Args:
            provider: 模型供应商，'deepseek' 或 'qwen'
        """
        providers = {
            "deepseek": {
                "api_key": settings.LLM_API_KEY,
                "api_url": settings.LLM_API_URL,
                "model": settings.LLM_MODEL,
            },
            "qwen": {
                "api_key": settings.QWEN_API_KEY,
                "api_url": settings.QWEN_API_URL,
                "model": settings.QWEN_MODEL,
            },
        }
        config = providers.get(provider, providers["deepseek"])
        self.api_key = config["api_key"]
        self.api_url = config["api_url"]
        self.model = config["model"]

    def chat(self, messages, stream=False, temperature=0.7, max_tokens=2048):
        """发送对话请求到 LLM API。

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            stream: 是否使用流式输出
            temperature: 生成温度
            max_tokens: 最大生成 token 数

        Returns:
            API 响应文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60,
                stream=stream,
            )
            response.raise_for_status()

            if stream:
                return self._handle_stream(response)
            else:
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            raise

    def _stream_lines(self, response):
        for line in response.iter_lines(chunk_size=1, decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue

            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break

            yield data_str

    def _extract_delta_content(self, data_str):
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return ""

        choices = data.get("choices") or []
        if not choices:
            return ""

        delta = choices[0].get("delta") or {}
        return delta.get("content") or ""

    def _handle_stream(self, response):
        """处理流式响应。"""
        full_content = ""
        for data_str in self._stream_lines(response):
            full_content += self._extract_delta_content(data_str)
        return full_content

    def chat_stream(self, messages, temperature=0.7, max_tokens=2048):
        """流式调用 LLM API，逐个 yield 文本块。"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120,
                stream=True,
            )
            response.raise_for_status()

            for data_str in self._stream_lines(response):
                content = self._extract_delta_content(data_str)
                if content:
                    yield content

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM 流式 API 请求失败: {e}")
            raise
