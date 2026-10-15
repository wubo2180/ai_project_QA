"""Dify 知识库（Dataset）API 调用模块。

对接 Dify 的 Dataset API，用于查询知识库、列出知识库中的文档。
注意：知识库 API 使用独立的 dataset-xxx 密钥（与对话用的 app-xxx 不同）。
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class DifyDatasetClient:
    """Dify 知识库 API 客户端。"""

    def __init__(self):
        self.base_url = (settings.DIFY_DATASET_BASE_URL or "").rstrip("/")
        self.api_key = settings.DIFY_DATASET_API_KEY

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_datasets(self, page=1, limit=100):
        """获取知识库列表。"""
        url = f"{self.base_url}"
        params = {"page": page, "limit": limit}
        resp = requests.get(url, headers=self._headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def find_dataset_by_name(self, name):
        """按名称查找知识库，返回匹配的第一个知识库字典，找不到返回 None。"""
        datasets = self.list_datasets(limit=100)
        for ds in datasets:
            if ds.get("name") == name:
                return ds
        # 名称完全匹配失败时，尝试去除空白后匹配
        target = (name or "").strip()
        for ds in datasets:
            if (ds.get("name") or "").strip() == target:
                return ds
        return None

    def list_documents(self, dataset_id, page=1, limit=100, keyword=None):
        """列出指定知识库下的文档。

        返回 (documents, total)。
        """
        url = f"{self.base_url}/{dataset_id}/documents"
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        resp = requests.get(url, headers=self._headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", []), data.get("total", 0)
