"""大模型 API 调用模块。"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """通用 LLM API 客户端，兼容 OpenAI 格式的接口。"""

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_url = settings.LLM_API_URL
        self.model = settings.LLM_MODEL

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

    def _handle_stream(self, response):
        """处理流式响应。"""
        full_content = ""
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        full_content += content
                    except json.JSONDecodeError:
                        continue
        return full_content
