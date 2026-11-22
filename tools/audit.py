# -*- coding: utf-8 -*-
"""课程体检：按"面向零基础"的硬指标逐课打分，找出结构缺失、代码没注释、交互缺失的课。

用法：
    python tools/audit.py            # 全量表格
    python tools/audit.py --bad      # 只看不达标的课
判据（任一不达标即列入待修）：
    goal/scene/term/pitfall/lab/quiz/check 七类块齐全
    每个代码块至少一行注释（# 或 //）
    每课至少 3 条术语、2 道自测
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
BLOCKS = ["goal", "scene", "term", "pitfall", "lab", "quiz", "check", "note", "sandbox"]


def parse(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    fm, body = "", raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        fm, body = raw[3:end], raw[end + 4:]
    meta = {}
    for line in fm.split("\n"):
        m = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip().strip('"')
    meta["status"] = meta.get("status", "live")
    meta["title"] = meta.get("title", "")

    blocks = {b: 0 for b in BLOCKS}
    for b in BLOCKS:
        blocks[b] = len(re.findall(r"^:::" + b + r"\b", body, re.M))

    # 代码块：```lang ... ```（只检查真代码；无语言的块是示意图/报告输出，不要求注释）
    CODE_LANGS = {"bash", "sh", "shell", "tcl", "python", "py", "make", "makefile", "csh", "tcsh", "awk", "sed", "perl"}
    codes = re.findall(r"^```(\w*)\n(.*?)^```", body, re.S | re.M)
    no_cmt = 0
    ncode = 0
    for lang, code in codes:
        if lang.lower() not in CODE_LANGS:
            continue
        ncode += 1
        lines = [l for l in code.split("\n") if l.strip()]
        if not any(l.lstrip().startswith(("#", "//", "/*", "*")) for l in lines):
            no_cmt += 1

    terms = re.findall(r"^:::term\s+(.+)$", body, re.M)
    quiz = re.findall(r"^:::quiz\n(.*?)^:::", body, re.S | re.M)
    nq = 0
    for q in quiz:
        nq += len([l for l in q.split("\n") if "|" in l])

    chapters = len(re.findall(r"^## ", body, re.M))
    cn = len(re.findall(r"[\u4e00-\u9fa5]", body))
    return {
        "id": meta.get("id", os.path.basename(path)[:-3]),
        "no": meta.get("no", ""),
        "stage": meta.get("stage", ""),
        "hours": float((meta.get("hours") or 0) or 0),
        "title": meta.get("title", ""),
        "status": meta["status"],
        "blocks": blocks,
        "codes": ncode,
        "no_cmt": no_cmt,
        "terms": len(terms),
        "quizzes": nq,
        "chapters": chapters,
        "cn": cn,
    }


def main():
    rows = []
    for name in sorted(os.listdir(CONTENT)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        rows.append(parse(os.path.join(CONTENT, name)))

    bad = []
    print(f"{'no':>3} {'id':<22} {'h':>4} {'ch':>3} {'字':>6} {'块(g/s/t/p/l/q/c)':<20} {'码':>3} {'无注':>4} {'术语':>4} {'题':>3}")
    for r in rows:
        b = r["blocks"]
        flags = f"{b['goal']}/{b['scene']}/{b['term']}/{b['pitfall']}/{b['lab']}/{b['quiz']}/{b['check']}"
        miss = [k for k in ("goal", "scene", "term", "pitfall", "lab", "quiz", "check") if b[k] == 0]
        problems = []
        if miss:
            problems.append("缺块:" + ",".join(miss))
        if r["no_cmt"]:
            problems.append(f"{r['no_cmt']} 个代码块没注释")
        if r["terms"] < 3:
            problems.append(f"术语仅 {r['terms']} 条")
        if r["quizzes"] < 2:
            problems.append(f"自测仅 {r['quizzes']} 题")
        if problems:
            bad.append((r, problems))
        print(f"{r['no']:>3} {r['id']:<22} {r['hours']:>4} {r['chapters']:>3} {r['cn']:>6} {flags:<20} "
              f"{r['codes']:>3} {r['no_cmt']:>4} {r['terms']:>4} {r['quizzes']:>3}"
              + ("   ← " + "; ".join(problems) if problems and "--bad" in sys.argv else ""))

    tot_h = sum(r["hours"] for r in rows)
    tot_cn = sum(r["cn"] for r in rows)
    print(f"\n合计：{len(rows)} 课 / {tot_h:g} 学时 / 汉字 {tot_cn} / "
          f"代码块 {sum(r['codes'] for r in rows)}（{sum(r['no_cmt'] for r in rows)} 个无注释）/ "
          f"术语 {sum(r['terms'] for r in rows)} / 自测 {sum(r['quizzes'] for r in rows)}")
    print(f"不达标课程：{len(bad)} / {len(rows)}")
    for r, p in bad:
        print(f"  - {r['no']:>3} {r['id']:<22} {'; '.join(p)}")


if __name__ == "__main__":
    main()
