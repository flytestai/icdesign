#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学习计时规则的静态回归。

规则（2026-11-27 调整后）：
  1. 课页不在前台（tab 隐藏 或 窗口失焦）→ 立刻停；
  2. 课页在前台，但超过 10 分钟没有任何操作 → 停止累计；
  3. 恢复操作 / 切回前台 → 从恢复那一刻继续，不补算中间的空档。

这里只做源码级断言：不启动浏览器，但把上面三条对应的实现点逐一钉住，
避免后续调整把阈值或事件绑定改回去（比如又变回 120 秒）。

用法： python tools/check_study_timer.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "web", "assets", "app.js")

fail = []


def need(cond, msg):
    if not cond:
        fail.append(msg)


def main():
    src = open(JS, encoding="utf-8").read()

    # ---- 规则 1：前台判定必须同时看 hidden 和 hasFocus
    m = re.search(r"function active\(\)\s*\{([^}]*)\}", src)
    need(m, "找不到 active() 前台判定函数")
    if m:
        body = m.group(1)
        need("document.hidden" in body, "active() 没有检查 document.hidden（切 tab 不会停表）")
        need("document.hasFocus()" in body, "active() 没有检查 document.hasFocus()（窗口失焦不会停表）")

    # 失焦与可见性变化必须触发重新判定
    need(re.search(r"addEventListener\('blur'", src), "缺少 blur 监听：窗口失焦时不会停表")
    need(re.search(r"addEventListener\('focus'", src), "缺少 focus 监听：窗口回焦时不会恢复")
    need(re.search(r"visibilitychange", src), "缺少 visibilitychange 监听：切换 tab 时不会停表")
    need(re.search(r"addEventListener\('pagehide'", src), "缺少 pagehide 监听：关页面时尾数会丢")

    # ---- 规则 2：空闲阈值必须是 10 分钟
    m2 = re.search(r"var IDLE_MS\s*=\s*(\d+)\s*;", src)
    need(m2, "找不到 IDLE_MS 定义")
    if m2:
        ms = int(m2.group(1))
        need(ms == 600000, "空闲阈值是 %d ms，应为 600000（10 分钟）" % ms)

    # 结算公式必须把空闲截止点算进去，否则超时后仍会继续累计
    need(re.search(r"Math\.min\(now,\s*last \+ IDLE_MS\)", src),
         "sample() 的结算没有按 last + IDLE_MS 截断，超时后会多算")

    # ---- 规则 3：恢复操作要能唤醒计时
    events = ["scroll", "keydown", "input", "pointerdown", "touchstart", "wheel"]
    for ev in events:
        need("'" + ev + "'" in src, "缺少交互事件 %s，该操作无法恢复计时" % ev)
    need("'mousemove'" in src,
         "缺少 mousemove 监听：只动鼠标（不滚动）无法唤醒计时")

    # 每个交互都必须先确认在前台，再把 last 推到当前时刻
    need(re.search(r"function markActive\(\)\s*\{[^}]*last\s*=\s*now", src, re.S),
         "markActive() 没有把 last 更新到当前时刻，恢复操作后仍会被判为空闲")

    # mousemove 要有节流，避免每帧都结算
    need(re.search(r"lastMoveMark\s*<\s*2000", src),
         "mousemove 没有节流，会产生高频采样")

    # ---- 状态提示要能说清为什么停
    for kw in ["课页不在前台", "10 分钟无操作"]:
        need(kw in src, "计时状态提示缺少「%s」的说明，用户不知道为何不计时" % kw)

    if fail:
        print("FAIL")
        for f in fail:
            print(" -", f)
        return 1
    print("OK: 前台判定 / 10 分钟空闲阈值 / 恢复唤醒 / 状态提示 全部符合预期")
    return 0


if __name__ == "__main__":
    sys.exit(main())