import requests

url = "http://127.0.0.1:8000/mcp"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
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
r = requests.post(url, headers=headers, json=body)
print("状态码:", r.status_code)
print("返回:", r.text[:500])