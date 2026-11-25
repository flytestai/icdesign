#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地测试：mock OpenAI 服务 + 测试 AI 配置/聊天全链路。"""
import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, "tools")


class MockAI(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n))
        auth = self.headers.get("Authorization", "")
        sys_msg = next((m["content"][:60] for m in body.get("messages", []) if m["role"] == "system"), "")
        reply = "MOCK回复（模型=%s，带课程上下文=%s，key前缀=%s）" % (
            body.get("model"), bool(sys_msg), auth[7:12])
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": reply}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8999), MockAI)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("mock AI on :8999")

BASE = "http://127.0.0.1:8711"
TOKEN = None


def api(path, data=None, method=None):
    req = urllib.request.Request(BASE + path, method=method or ("POST" if data else "GET"))
    if TOKEN:
        req.add_header("Cookie", "ic_session=" + TOKEN)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.add_header("Cookie", "ic_session=" + TOKEN)
        req.data = json.dumps(data, ensure_ascii=False).encode()
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


# 登录
import re
resp = urllib.request.Request(BASE + "/api/auth/login", method="POST")
resp.add_header("Content-Type", "application/json")
resp.data = json.dumps({"account": "weizhen", "password": "wz729729"}).encode()
with urllib.request.urlopen(resp, timeout=30) as r:
    TOKEN = re.search(r"ic_session=([a-f0-9]{64})", r.headers.get("Set-Cookie", "")).group(1)
print("登录 OK")

print("1) 未配置时 settings:", api("/api/ai/settings")[1]["configured"] == False)
try:
    api("/api/ai/chat", {"messages": [{"role": "user", "content": "hi"}]})
    print("2) 未配置聊天应报错: FAIL")
except urllib.error.HTTPError as e:
    print("2) 未配置聊天报错:", e.code, json.loads(e.read())["detail"] == "NO_AI_CONFIG")

print("3) 保存配置:", api("/api/ai/settings", {"provider": "openai", "base_url": "http://127.0.0.1:8999/v1", "api_key": "sk-test-123456", "model": "mock-model"})[1])
print("4) 配置后 settings:", api("/api/ai/settings")[1]["configured"] == True)

st, res = api("/api/ai/chat", {"messages": [{"role": "user", "content": "什么是DRC"}], "lesson": "01-01-linux-01-intro"})
print("5) 课程页聊天:", st == 200, "|", res["reply"][:50])

st, res = api("/api/ai/chat", {"messages": [{"role": "user", "content": "你好"}]})
print("6) 非课程页聊天:", st == 200, "|", res["reply"][:40])

try:
    api("/api/ai/settings", {"provider": "openai", "base_url": "http://192.168.1.1/v1", "api_key": "k", "model": "m"})
    print("7) 内网拦截: FAIL")
except urllib.error.HTTPError as e:
    print("7) 内网拦截:", e.code, json.loads(e.read())["detail"] == "接口地址不允许指向内网/本机")

print("8) 修改配置不传 key（沿用旧 key）:", api("/api/ai/settings", {"provider": "openai", "base_url": "http://127.0.0.1:8999/v1", "api_key": "", "model": "mock-model2"})[1])
st, res = api("/api/ai/chat", {"messages": [{"role": "user", "content": "再问一次"}]})
print("9) 旧 key 生效:", st == 200, "|", res["reply"][:40])
