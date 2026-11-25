#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 对话持久化测试：按用户+课程隔离 / 刷新后可见 / 超长自动压缩 / 主动清空。

    python tools/_test_chat.py
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8711"
COOKIE = ""


def api(path, data=None, method=None, cookie=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Content-Type", "application/json")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def login(account, password):
    url = BASE + "/api/auth/login"
    req = urllib.request.Request(url, data=json.dumps({"account": account, "password": password}).encode())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            for h in r.headers.get_all("Set-Cookie") or []:
                if h.startswith("ic_session="):
                    return h.split(";")[0]
    except urllib.error.HTTPError as e:
        print("登录失败", e.code, e.read()[:100])
    return None


ck = login("weizhen", "wz729729")
if not ck:
    print("需要先登录管理员，测试退出")
    sys.exit(1)
print("登录 OK")

L1 = "01-07-tcl-01-start"
L2 = "01-08-tcl-02-vars"

# 0. 初始为空
st, res = api("/api/ai/chat/history?lesson=" + L1, cookie=ck)
print("1) 初始历史为空:", st == 200 and res["messages"] == [])

# 1. 保存 L1 的两轮
msgs1 = [
    {"role": "user", "content": "什么是 Tcl？"},
    {"role": "assistant", "content": "Tcl 是一种脚本语言。"},
    {"role": "user", "content": "set 怎么用？"},
    {"role": "assistant", "content": "set a 1 用来赋值。"},
]
st, res = api("/api/ai/chat/history", {"lesson": L1, "messages": msgs1}, cookie=ck)
print("2) 保存 L1 对话:", st == 200 and res["ok"], "| 条数 =", res.get("count"))

# 2. 重新读取（模拟刷新）
st, res = api("/api/ai/chat/history?lesson=" + L1, cookie=ck)
print("3) 刷新后能读到:", len(res["messages"]) == 4, "| 最后一条:", res["messages"][-1]["content"][:12])

# 3. 另一节课隔离
st, res = api("/api/ai/chat/history?lesson=" + L2, cookie=ck)
print("4) 另一节课为空（隔离）:", res["messages"] == [])

api("/api/ai/chat/history", {"lesson": L2, "messages": [{"role": "user", "content": "变量是什么"}]}, cookie=ck)
st, r1 = api("/api/ai/chat/history?lesson=" + L1, cookie=ck)
st, r2 = api("/api/ai/chat/history?lesson=" + L2, cookie=ck)
print("5) 两课互不干扰:", len(r1["messages"]) == 4 and len(r2["messages"]) == 1)

# 4. 超长自动压缩（30 条 > CHAT_KEEP_TURNS=12）
big = []
for i in range(15):
    big.append({"role": "user", "content": "第%d个问题：什么是 cell %d？" % (i + 1, i + 1)})
    big.append({"role": "assistant", "content": "回答%d" % (i + 1)})
st, res = api("/api/ai/chat/history", {"lesson": L2, "messages": big}, cookie=ck)
print("6) 超长压缩后保留条数:", res.get("count"), "| compressed =", res.get("compressed"))
st, res = api("/api/ai/chat/history?lesson=" + L2, cookie=ck)
print("7) 摘要已生成:", bool(res.get("digest")), "| 摘要片段:", (res.get("digest") or "")[:40])

# 5. 主动清空
st, res = api("/api/ai/chat/history?lesson=" + L1, method="DELETE", cookie=ck)
print("8) 清空 L1:", st == 200 and res["ok"])
st, res = api("/api/ai/chat/history?lesson=" + L1, cookie=ck)
print("9) 清空后为空:", res["messages"] == [])
st, res = api("/api/ai/chat/history?lesson=" + L2, cookie=ck)
print("10) 清空 L1 不影响 L2:", len(res["messages"]) > 0)

# 清理
api("/api/ai/chat/history?lesson=" + L2, method="DELETE", cookie=ck)
print("清理完成")