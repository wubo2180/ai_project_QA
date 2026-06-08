"""网页搜索模块（使用 DuckDuckGo，无需 API Key）。"""
import logging
import urllib.parse

import requests

logger = logging.getLogger(__name__)

# 常见的 User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """使用 DuckDuckGo 的 HTML 页面解析进行搜索。

    返回: [{"title": ..., "snippet": ..., "url": ...}, ...]
    """
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"搜索请求失败: {e}")
        return []

    results = _parse_duckduckgo_html(resp.text, max_results)
    return results


def _parse_duckduckgo_html(html: str, max_results: int) -> list[dict]:
    """从 DuckDuckGo HTML 页面解析搜索结果。"""
    results = []
    # 用简单的方式提取结果：找 class="result__body" 的区域
    # 按结果块分割
    import re

    # 匹配 result__body 块
    blocks = re.findall(
        r'<div class="result__body[^"]*".*?</div>\s*</div>\s*</div>',
        html,
        re.DOTALL,
    )

    for block in blocks:
        if len(results) >= max_results:
            break

        # 提取标题
        title_match = re.search(
            r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL
        )
        title = ""
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()

        # 提取摘要
        snippet_match = re.search(
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL
        )
        snippet = ""
        if snippet_match:
            snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip()

        # 提取 URL
        url_match = re.search(r'href="(https?://[^"]+)"', block)
        url = url_match.group(1) if url_match else ""

        if title or snippet:
            results.append({
                "title": title,
                "snippet": snippet,
                "url": url,
            })

    # 如果上面的正则没匹配到，用备用方法
    if not results:
        # 简单方法：找所有的 <a> 标签
        all_links = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="(https?://[^"]*)"[^>]*>(.*?)</a>',
            html,
        )
        all_snippets = re.findall(
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL
        )
        for i, (url, title_html) in enumerate(all_links[:max_results]):
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            snippet = ""
            if i < len(all_snippets):
                snippet = re.sub(r"<[^>]+>", "", all_snippets[i]).strip()
            results.append({"title": title, "snippet": snippet, "url": url})

    return results


def format_search_context(query: str, results: list[dict]) -> str:
    """将搜索结果格式化为 LLM 上下文。"""
    if not results:
        return ""

    lines = [
        f"以下是关于「{query}」的联网搜索结果（仅供参考）：",
        "---",
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        if r["snippet"]:
            lines.append(f"   {r['snippet']}")
        lines.append("")

    return "\n".join(lines)
