import requests

# 测试健康检查
r = requests.get("http://127.0.0.1:8000/api/health/")
print("健康检查:", r.json())

# 测试 Excel 导出
content = """| 姓名 | 年龄 | 城市 |
|---|---|---|
| 张三 | 25 | 北京 |
| 李四 | 30 | 上海 |
| 王五 | 28 | 广州 |"""

r2 = requests.post(
    "http://127.0.0.1:8000/api/export-excel/",
    json={"content": content, "filename": "测试导出"},
)
print(f"导出状态码: {r2.status_code}")
print(f"文件类型: {r2.headers.get('Content-Type', '')}")
if r2.status_code == 200:
    # 保存文件验证
    with open("test_export.xlsx", "wb") as f:
        f.write(r2.content)
    print("文件大小:", len(r2.content), "bytes")
    print("✅ 导出成功!")
else:
    print("❌ 导出失败:", r2.json())
