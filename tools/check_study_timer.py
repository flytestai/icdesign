#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学习计时的静态回归（源码级断言，配合 check_timer_e2e.js 的行为测试）。

现行规则：
  1. 本页不在前台（tab 隐藏 / 窗口失焦）→ 立即停，不补算；
  2. 前台但距最后一次真实操作超过 10 分钟 → 判挂机，
     该活动窗口内已累计的部分要整段退回（不白送阈值）；
  3. 批次先落 localStorage 再上报，关页/断网不丢；
  4. 上报带 batch_id，服务端按 (user, batch_id) 去重；
  5. 同一页面多标签只让一个 leader 上报，避免重复计入。

用法： python tools/check_study_timer.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "web", "assets", "app.js")
PY = os.path.join(ROOT, "server", "app.py")

fail = []


def need(cond, msg):
    if not cond:
        fail.append(msg)


def main():
    src = open(JS, encoding="utf-8").read()
    py = open(PY, encoding="utf-8").read()

    # ---- 1. 前台判定 ----
    m = re.search(r"function active\(\)\s*\{([^}]*)\}", src)
    need(m, "找不到 active() 前台判定")
    if m:
        need("document.hidden" in m.group(1), "active() 未检查 document.hidden（切 tab 不停表）")
        need("document.hasFocus()" in m.group(1), "active() 未检查 hasFocus（失焦不停表）")
    for ev in ["'blur'", "'focus'", "visibilitychange", "'pagehide'"]:
        need(ev in src, "缺少 %s 监听，状态切换时不会停/续计时" % ev)

    # ---- 2. 空闲阈值与退回 ----
    m2 = re.search(r"var IDLE_MS\s*=\s*(\d+)\s*;", src)
    need(m2, "找不到 IDLE_MS")
    if m2:
        need(int(m2.group(1)) == 600000, "IDLE_MS 应为 600000（10 分钟），实际 %s" % m2.group(1))

    m3 = re.search(r"function tick\(\)\s*\{(.*?)\n      \}", src, re.S)
    need(m3, "找不到 tick() 采样函数")
    if m3:
        body = m3.group(1)
        # 必须用「距上次真实操作」判断空闲，而不是距上次采样
        need("now - last > IDLE_MS" in body,
             "tick() 未用 now-last 判断空闲（用 lastTick 会永远判不出空闲）")
        need("markIdle()" in body, "tick() 判定空闲后未调用 markIdle() 退回")
        need("accMs += gap" in body, "tick() 未按真实流逝时间累加")

    m4 = re.search(r"function markIdle\(\)\s*\{(.*?)\n      \}", src, re.S)
    need(m4, "找不到 markIdle() 退回函数")
    if m4:
        b = m4.group(1)
        need("accMs -= need" in b or "accMs -= winAcc" in b,
             "markIdle() 没有从 accMs 里扣回已累计的挂机时段")
        need("batches" in b, "markIdle() 未处理已切成批次的部分，退回不彻底")

    # 不允许出现旧的「乐观累计到阈值」写法
    need("Math.min(now, last + IDLE_MS)" not in src,
         "仍存在乐观累计写法（会把 IDLE_MS 白送出去）")

    # ---- 3. 批次持久化 ----
    need("loadQueue" in src and "saveQueue" in src, "缺少队列持久化函数")
    need("localStorage.setItem(LS_BATCH" in src, "批次未写入 localStorage，关页会丢")
    m5 = re.search(r"function flush\(leaving\)\s*\{(.*?)\n      \}", src, re.S)
    if m5:
        b = m5.group(1)
        need("saveQueue()" in b, "flush() 没有先落盘再上报，关页会丢数据")

    # ---- 4. 多标签去重 ----
    need("LS_LEADER" in src and "isLeader" in src, "缺少多标签 leader 选举，会重复计入")

    # ---- 5. 服务端 batch_id 必填与去重 ----
    need(re.search(r"batch_id:\s*UUID", py), "服务端 batch_id 应为必填（UUID 而非 Optional）")
    need("study_time_receipts(user_id,batch_id,ts)" in py,
         "回执表未记录 ts，无法做过期清理")
    need("ON CONFLICT(user_id,batch_id) DO NOTHING" in py,
         "服务端未按 (user, batch_id) 幂等去重")
    need("lesson not in _study_pages()" in py, "服务端未校验学习页白名单")

    # ---- 6. 白名单覆盖 ----
    m6 = re.search(r"var PAGE_STUDY\s*=\s*\{(.*?)\};", src, re.S)
    need(m6, "找不到 PAGE_STUDY 白名单")
    if m6:
        for pg in ["playground", "quiz", "exam", "glossary", "abbr",
                   "cheatsheet", "search", "progress", "leaderboard"]:
            need(pg + ":" in m6.group(1), "PAGE_STUDY 缺少 %s，该页不计时" % pg)

    # ---- 7. 状态文案 ----
    for kw in ["本页不在前台", "10 分钟无操作"]:
        need(kw in src, "状态提示缺少「%s」" % kw)

    if fail:
        print("FAIL")
        for f in fail:
            print(" -", f)
        return 1
    print("OK: 前台判定 / 空闲退回 / 队列持久化 / 多标签去重 / 服务端幂等 全部符合预期")
    return 0


if __name__ == "__main__":
    sys.exit(main())