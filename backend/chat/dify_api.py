"""Dify Chatflow API 调用模块。

对接 Dify 的 /chat-messages 接口，支持流式（streaming）与阻塞（blocking）两种模式。
Dify 自身负责多轮对话上下文：通过返回的 conversation_id 维持会话。
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DifyClient:
    """Dify Chatflow API 客户端。"""

    def __init__(self):
        self.api_url = (settings.DIFY_API_URL or "").rstrip("/")
        self.api_key = settings.DIFY_API_KEY

    @property
    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(self, query, user, conversation_id=None, response_mode="streaming", inputs=None):
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": response_mode,
            "user": user or "web-user",
        }
        # 仅当有有效 conversation_id 时才传递，继续已有会话
        if conversation_id:
            payload["conversation_id"] = conversation_id
        return payload

    def chat(self, query, user="web-user", conversation_id=None, inputs=None):
        """阻塞模式调用，返回 (answer, conversation_id)。"""
        url = f"{self.api_url}/chat-messages"
        payload = self._build_payload(
            query, user, conversation_id, response_mode="blocking", inputs=inputs
        )
        try:
            resp = requests.post(url, headers=self._headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("answer", ""), data.get("conversation_id", conversation_id)
        except requests.exceptions.RequestException as e:
            logger.error("Dify API 请求失败: %s", e)
            raise

    def chat_stream(self, query, user="web-user", conversation_id=None, inputs=None):
        """流式模式调用。

        逐块 yield 字典事件：
          {"type": "chunk", "content": "..."}
          {"type": "conversation", "conversation_id": "..."}
          {"type": "done"}
          {"type": "error", "content": "..."}
        """
        url = f"{self.api_url}/chat-messages"
        payload = self._build_payload(
            query, user, conversation_id, response_mode="streaming", inputs=inputs
        )

        try:
            resp = requests.post(
                url,
                headers=self._headers,
                json=payload,
                timeout=180,
                stream=True,
            )
            resp.raise_for_status()
            resp.encoding = "utf-8"

            conv_id_sent = conversation_id
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue

                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("event")

                # 新会话 id 回传给前端，便于下一轮继续上下文
                new_conv_id = event.get("conversation_id")
                if new_conv_id and new_conv_id != conv_id_sent:
                    conv_id_sent = new_conv_id
                    yield {"type": "conversation", "conversation_id": new_conv_id}

                if event_type in ("message", "agent_message"):
                    answer = event.get("answer", "")
                    if answer:
                        yield {"type": "chunk", "content": answer}
                elif event_type == "message_end":
                    yield {"type": "done"}
                elif event_type == "error":
                    msg = event.get("message") or event.get("code") or "Dify 返回错误"
                    yield {"type": "error", "content": str(msg)}

        except requests.exceptions.HTTPError as e:
            body = ""
            try:
                body = e.response.text[:500] if e.response is not None else ""
            except Exception:
                pass
            logger.error("Dify 流式 API HTTP 错误: %s, 响应: %s", e, body)
            yield {"type": "error", "content": "对话服务请求失败"}
        except requests.exceptions.RequestException as e:
            logger.error("Dify 流式 API 请求失败: %s", e)
            yield {"type": "error", "content": "对话服务暂时不可用，请稍后重试"}
