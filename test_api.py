"""快速测试对话列表 API"""
import requests
r = requests.get("http://127.0.0.1:8000/api/conversations/")
data = r.json()
print(f"对话数: {len(data)}")
for c in data:
    print(f"  {c['id'][:8]} - {c['title']} ({c.get('message_count', 0)}条)")
