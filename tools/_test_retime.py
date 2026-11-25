#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重学计时测试：无论是否清除进度，重复学习都要累计时长并计入排名。

    python tools/_test_retime.py
"""
import json
import sys
import urllib.error
import urllib.request
import time

BASE = "http://127.0.0.1:8711"


def call(p, d=None, ck=None, method=None):
    body = json.dumps(d).encode() if d is not None else None
    req = urllib.request.Request(BASE + p, data=body,
                                 method=method or ("POST" if d is not None else "GET"))
    req.add_header("Content-Type", "application/json")
    if ck:
        req.add_header("Cookie", ck)
    try:
        with urllib.request.urlopen(req, timeout=20) as x:
            raw = x.read()
            return x.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        b = e.read()
        try:
            j = json.loads(b) if b else {}
        except Exception:
            j = {}
        return e.code, j


def login(a, p):
    req = urllib.request.Request(BASE + "/api/auth/login",
                                 data=json.dumps({"account": a, "password": p}).encode())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as x:
            for h in x.headers.get_all("Set-Cookie") or []:
                if h.startswith("ic_session="):
                    return h.split(";")[0]
    except urllib.error.HTTPError:
        return None
    return None


ck = login("weizhen", "wz729729")
if not ck:
    print("登录失败")
    sys.exit(1)
print("登录 OK")

cat = json.load(open("web/data/catalog.json", encoding="utf-8"))
L = cat["lessons"][0]
lid = L["id"]
chs = [c["id"] for c in L["chapters"]]

# 干净起点
call("/api/progress", ck=ck, method="DELETE")
print("\n[A] 起点：清空进度")
base = call("/api/study-time", ck=ck)[1]["total"]
print("    当前累计时长:", base, "秒")

# --- 场景 1：第一次学，记 120 秒 ---
call("/api/study-time", {"lesson": lid, "seconds": 120}, ck=ck)
t1 = call("/api/study-time", ck=ck)[1]["total"]
print("\n[1] 第一次学 120 秒 → 累计:", t1, "秒", "✓" if t1 == base + 120 else "✗")

# 学完这一课
call("/api/progress", {"items": [{"lesson": lid, "chapter": c, "done": True} for c in chs]}, ck=ck)
d = call("/api/progress", ck=ck)[1]
print("    进度:", len([x for x in d["items"] if x["lesson"] == lid]), "章")

# --- 场景 2：不清进度，重学一遍，再记 90 秒 ---
call("/api/study-time", {"lesson": lid, "seconds": 90}, ck=ck)
t2 = call("/api/study-time", ck=ck)[1]["total"]
print("\n[2] 不清进度重学 90 秒 → 累计:", t2, "秒",
      "✓ 时长累加" if t2 == t1 + 90 else "✗")

# --- 场景 3：清除进度，再重学 60 秒 ---
call("/api/progress/" + lid, ck=ck, method="DELETE")
d = call("/api/progress", ck=ck)[1]
after_clear = len([x for x in d["items"] if x["lesson"] == lid])
t3_before = call("/api/study-time", ck=ck)[1]["total"]
print("\n[3] 清除进度后：该课剩余", after_clear, "章（应为 0）")
print("    清除后时长仍为:", t3_before, "秒", "✓ 不受影响" if t3_before == t2 else "✗ 被清掉了")

call("/api/study-time", {"lesson": lid, "seconds": 60}, ck=ck)
t3 = call("/api/study-time", ck=ck)[1]["total"]
print("    重学 60 秒 → 累计:", t3, "秒", "✓" if t3 == t2 + 60 else "✗")

# --- 场景 4：清空全部进度也要保留时长 ---
call("/api/progress", ck=ck, method="DELETE")
t4 = call("/api/study-time", ck=ck)[1]["total"]
print("\n[4] 清空全部进度 → 累计时长:", t4, "秒",
      "✓ 完整保留" if t4 == t3 else "✗ 被清掉了")

# --- 场景 5：排行榜应反映累计时长 ---
lb = call("/api/leaderboard", ck=ck)[1]
me = [r for r in lb["rows"] if r["is_me"] or r["name"] == "魏振"]
if me:
    print("\n[5] 排行榜中我的时长:", me[0]["seconds"], "秒",
          "✓ 与累计一致" if me[0]["seconds"] == t4 else "✗ 不一致(%s vs %s)" % (me[0]["seconds"], t4))
    print("    时长分:", me[0]["time_pct"], "| 综合分:", me[0]["score"])

# 各课明细
st, detail = call("/api/study-time", ck=ck)
print("\n[6] 按课程明细:", {k: v for k, v in list(detail.get("by_lesson", {}).items())[:4]})

print("\n—— 说明：时长只增不减，与进度完全解耦；重学多少遍都会累加并计入排名 ——")