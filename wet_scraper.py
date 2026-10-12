import requests
import json

BASE = "http://127.0.0.1:8000/mcp"
DOC_URL = "https://your-domain.larkoffice.com/docx/YOUR_DOC_ID"

headers_base = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

session = requests.Session()
session_id = None

def mcp_call(method, params=None, req_id=1):
    global session_id
    headers = dict(headers_base)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    body = {"jsonrpc": "2.0", "method": method, "id": req_id, "params": params or {}}
    r = session.post(BASE, headers=headers, json=body)
    if not session_id:
        session_id = r.headers.get("Mcp-Session-Id") or r.headers.get("mcp-session-id")
    print(f"\n--- {method} 原始响应 ---")
    print("状态码:", r.status_code)
    print("响应体:", r.text[:2000])
    return r.text

# initialize
mcp_call("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"},
}, req_id=1)
mcp_call("notifications/initialized", {}, req_id=2)

# extract
mcp_call("tools/call", {
    "name": "extract",
    "arguments": {
        "action": "extract",
        "urls": [DOC_URL],
        "format": "markdown",
        "stealth": True,
    },
}, req_id=3)