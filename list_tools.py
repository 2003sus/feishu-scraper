import requests

url = "http://127.0.0.1:8000/mcp"
headers_base = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

session = requests.Session()

# ── 1. initialize，拿 session ID ──
body = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    },
}
r = session.post(url, headers=headers_base, json=body)
print("initialize 状态码:", r.status_code)

# 关键：从响应头里拿 session ID
session_id = r.headers.get("Mcp-Session-Id") or r.headers.get("mcp-session-id")
print("Session ID:", session_id)

if not session_id:
    print("没拿到 session ID，把完整响应头打印出来：")
    print(dict(r.headers))
    exit()

# 之后所有请求都带上 session ID
headers = {**headers_base, "Mcp-Session-Id": session_id}

# ── 2. 发 initialized 通知（协议要求）──
notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
session.post(url, headers=headers, json=notify)

# ── 3. tools/list ──
body2 = {"jsonrpc": "2.0", "method": "tools/list", "id": 2, "params": {}}
r2 = session.post(url, headers=headers, json=body2)
print("\n=== tools/list ===")
print(r2.text)