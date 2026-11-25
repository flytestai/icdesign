#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排行榜测试：学习时长上报 / 账号 uid 关联 / 综合排名与权重。

    python tools/_test_board.py
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8711"


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
    req = urllib.request.Request(BASE + "/api/auth/login",
                                 data=json.dumps({"account": account, "password": password}).encode())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            for h in r.headers.get_all("Set-Cookie") or []:
                if h.startswith("ic_session="):
                    return h.split(";")[0]
    except urllib.error.HTTPError:
        return None


ck = login("weizhen", "wz729729")
if not ck:
    print("登录失败")
    sys.exit(1)
print("登录 OK")

# 1. 未登录访问应 401
st, _ = api("/api/leaderboard")
print("1) 未登录访问排行榜被拒:", st == 401)

# 2. 上报学习时长
st, res = api("/api/study-time", {"lesson": "01-07-tcl-01-start", "seconds": 120}, cookie=ck)
print("2) 上报时长:", st == 200 and res["added"] == 120)
st, res = api("/api/study-time", {"lesson": "01-08-tcl-02-vars", "seconds": 60}, cookie=ck)
st, res = api("/api/study-time", cookie=ck)
print("3) 累计时长:", res["total"] >= 180, "| 总计 =", res["total"], "秒")

# 3. 非法参数
try:
    st, res = api("/api/study-time", {"lesson": "bad/lesson", "seconds": 10}, cookie=ck)
    print("4) 非法课程 ID 被拒:", st == 400)
except Exception as e:
    print("4) 非法课程 ID 被拒: 异常", e)
st, res = api("/api/study-time", {"lesson": "01-07-tcl-01-start", "seconds": -5}, cookie=ck)
print("5) 负数时长被拒:", st in (422, 400))

# 4. uid 关联
st, res = api("/api/auth/link-uid", {"uid": "uboardtest1234"}, cookie=ck)
print("6) 登记设备 uid:", st == 200 and res["ok"])
st, res = api("/api/auth/link-uid", {"uid": "x"}, cookie=ck)
print("7) 非法 uid 被拒:", st == 400)

# 5. 排行榜
st, res = api("/api/leaderboard", cookie=ck)
print("8) 排行榜可访问:", st == 200 and "rows" in res)
if st == 200:
    print("   权重:", res["weights"], "| 章节总数:", res["total_chapters"])
    for r in res["rows"][:5]:
        print("   #%d %s 完成 %d/%d 章 时长 %d 秒 进度分 %.1f 综合 %.1f%s"
              % (r["rank"], r["name"], r["done"], r["total"], r["seconds"],
                 r["progress_pct"], r["score"], "  <- 我" if r["is_me"] else ""))
    scores = [r["score"] for r in res["rows"]]
    print("9) 按综合分降序:", scores == sorted(scores, reverse=True))
    print("10) 标记了当前用户:", any(r["is_me"] for r in res["rows"]))
    print("11) 不含账号/手机号字段:", all("account" not in r and "phone" not in r for r in res["rows"]))