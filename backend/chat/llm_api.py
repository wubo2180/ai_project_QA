"""大模型 API 调用模块。"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """通用 LLM API 客户端，兼容 OpenAI 格式的接口。"""

    def __init__(self, provider="deepseek_flash"):
        """初始化 LLM 客户端。
        Args:
            provider: 模型 key，对应 settings.AVAILABLE_MODELS 中的键
                      （deepseek_flash / deepseek_pro / qwen_plus / qwen_max / gpt）
        """
        models = settings.AVAILABLE_MODELS
        # 找不到对应 provider 时回退到默认模型
        config = models.get(provider) or models.get("deepseek_flash") or next(iter(models.values()))
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
        # SSE 响应通常不带 charset，requests 会回退到 latin-1 导致中文乱码，强制 UTF-8
        response.encoding = "utf-8"
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

            yielded_any = False
            for data_str in self._stream_lines(response):
                content = self._extract_delta_content(data_str)
                if content:
                    yielded_any = True
                    yield content

            # 上游返回 200 但没有任何有效内容（常见于错误以非 SSE 的 JSON 返回）
            if not yielded_any:
                logger.warning("LLM 流式响应无有效内容，model=%s url=%s", self.model, self.api_url)

        except requests.exceptions.HTTPError as e:
            body = ""
            try:
                body = e.response.text[:500] if e.response is not None else ""
            except Exception:
                pass
            logger.error("LLM 流式 API HTTP 错误: %s, 响应: %s", e, body)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM 流式 API 请求失败: {e}")
            raise
