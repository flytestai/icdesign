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
    def do_GET(self):
        out = json.dumps({"data": [{"id": "mock-alpha"}, {"id": "mock-beta"}, {"id": "mock-gamma"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

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

# 新端点：拉取模型列表 / 删除配置
st, res = api("/api/ai/models", {"provider": "openai", "base_url": "http://127.0.0.1:8999/v1", "api_key": "sk-test-123456"})
print("10) 拉取模型列表(带key):", st == 200 and res["models"] == ["mock-alpha", "mock-beta", "mock-gamma"], "|", res["models"])

st, res = api("/api/ai/models", {"provider": "openai", "base_url": "http://127.0.0.1:8999/v1", "api_key": ""})
print("11) 拉取模型列表(不传key沿用已存):", st == 200 and len(res["models"]) == 3)

print("12) 删除配置:", api("/api/ai/settings", method="DELETE")[1])
print("13) 删除后 settings:", api("/api/ai/settings")[1]["configured"] == False)
try:
    api("/api/ai/models", {"provider": "openai", "base_url": "http://127.0.0.1:8999/v1", "api_key": ""})
    print("14) 删除后拉模型应报错: FAIL")
except urllib.error.HTTPError as e:
    print("14) 删除后拉模型报错:", e.code, "请先填写 API Key" in json.loads(e.read())["detail"])

# AI 问答笔记
st, res = api("/api/ai/notes", {"question": "什么是 DRC？", "answer": "DRC 是设计规则检查。", "lesson": "01-01-linux-01-intro"})
print("15) 保存问答笔记:", st == 200 and res.get("ok") and res["id"] > 0, "| id =", res.get("id"))
NID = res.get("id")

st, res = api("/api/ai/notes", {"question": "另一问", "answer": "另一答", "lesson": ""})
NID2 = res.get("id")

st, res = api("/api/ai/notes")
byid = {n["id"]: n for n in res["notes"]}
print("16) 笔记列表:", st == 200 and len(res["notes"]) >= 2, "| 共", len(res["notes"]), "条")
print("17) 笔记带课程:", byid.get(NID, {}).get("lesson") == "01-01-linux-01-intro")

try:
    api("/api/ai/notes", {"question": "", "answer": ""})
    print("18) 空内容应报错: FAIL")
except urllib.error.HTTPError as e:
    print("18) 空内容报错:", e.code)

st, res = api("/api/ai/notes/%d" % NID, method="DELETE")
print("19) 删除笔记:", st == 200 and res["ok"] is True)
try:
    api("/api/ai/notes/%d" % NID, method="DELETE")
    print("20) 重复删除报 404: FAIL")
except urllib.error.HTTPError as e:
    print("20) 重复删除报 404:", e.code == 404)
api("/api/ai/notes/%d" % NID2, method="DELETE")


