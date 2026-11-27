#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「继续学习」全路径回归（离线，不需要启动服务）。

直接调用 server/app.py 里的 next_lesson 逻辑太重（要 DB、要 session），
这里复刻同一套规则并断言关键路径：
  1. 全新账号 → 第一课；
  2. 学完阶段一、二 → 阶段三导读（不是 31a）；
  3. 学完导读 → 主线首课《Innovus 的使用》；
  4. 学完阶段三主线 → 阶段四（不中途插入 21 篇选学）；
  5. 刚看过参考页（3 天内）→ 回到该参考页；
  6. 参考页停留超 3 天 → 越过它继续主线。

用法： python tools/check_resume_path.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

RESUME_REF_SECONDS = 3 * 86400
cat = json.load(open(os.path.join(ROOT, "web", "data", "catalog.json"), encoding="utf-8"))
by_id = {L["id"]: L for L in cat["lessons"]}
order = cat["route"]
ch_of = {L["id"]: [c["id"] for c in L["chapters"]] for L in cat["lessons"]}


def resolve(done, last=None, last_age=0.0):
    """复刻 next_lesson 的判定顺序。"""
    def first_undone(lid):
        for ch in ch_of.get(lid, []):
            if (lid, ch) not in done:
                return ch
        return None

    if last and last in ch_of:
        is_ref = last not in set(order)
        if first_undone(last) and (not is_ref or last_age <= RESUME_REF_SECONDS):
            return last, first_undone(last), "resume"
    for lid in order:
        ch = first_undone(lid)
        if ch:
            return lid, ch, ("resume" if last == lid else "next-undone")
    return order[-1], "", "all-done"


def mark(done, lid):
    for ch in ch_of.get(lid, []):
        done.add((lid, ch))


cases = []
# 1) 全新
cases.append(("全新账号", resolve(set())[:2], ("01-01-linux-01-intro", "what")))

# 2) 学完阶段一二
d = set()
for L in cat["lessons"]:
    if L["stage"] in (1, 2):
        mark(d, L["id"])
cases.append(("学完阶段一二", resolve(d)[:2],
              (build.INNOVUS_GUIDE, cat["neighbors"][build.INNOVUS_GUIDE]["next"] and
               ch_of[build.INNOVUS_GUIDE][0])))

# 3) 再学完导读
mark(d, build.INNOVUS_GUIDE)
cases.append(("学完导读", resolve(d)[:2], ("03-02-innovus-start", ch_of["03-02-innovus-start"][0])))

# 4) 学完阶段三主线
for L in cat["lessons"]:
    if L["id"] in cat["route"] and L["stage"] == 3:
        mark(d, L["id"])
cases.append(("学完阶段三主线", resolve(d)[:2], ("04-01-icc2-plan", ch_of["04-01-icc2-plan"][0])))

# 5) 刚看过参考页
d2 = set(d)
ref = "03-01c-project-details"
cases.append(("3 天内看过参考页", resolve(d2, last=ref, last_age=3600)[:1], (ref,)))

# 6) 参考页已超期
cases.append(("参考页停留超 3 天", resolve(d2, last=ref, last_age=5 * 86400)[:1],
              ("04-01-icc2-plan",)))

fail = 0
for name, got, want in cases:
    if got != want:
        fail += 1
        print(f"FAIL {name}: 实际 {got} 期望 {want}")
    else:
        print(f"ok   {name} -> {got[0]}")

print("FAILED" if fail else f"全部 {len(cases)} 条路径通过")
sys.exit(1 if fail else 0)