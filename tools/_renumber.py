# -*- coding: utf-8 -*-
"""按 (stage, 文件名) 顺序重排课程编号，写回 front-matter 的 no 字段。"""
import io
import os
import re

CONTENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content")


def meta(path, key):
    s = io.open(path, encoding="utf-8").read()
    m = re.search(r"(?m)^" + key + r":\s*(.+)$", s)
    return m.group(1).strip() if m else ""


def main():
    rows = []
    for fn in os.listdir(CONTENT):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        p = os.path.join(CONTENT, fn)
        rows.append((int(meta(p, "stage") or 9), fn))
    rows.sort()
    for i, (stage, fn) in enumerate(rows):
        p = os.path.join(CONTENT, fn)
        s = io.open(p, encoding="utf-8").read()
        new = "%02d" % i
        s2 = re.sub(r"(?m)^no:\s*.+$", "no: " + new, s, count=1)
        if s2 == s and not re.search(r"(?m)^no:", s):
            # 没有 no 字段就补一个（放在 id 后面）
            s2 = re.sub(r"(?m)^(id:.*)$", r"\1\nno: " + new, s, count=1)
        io.open(p, "w", encoding="utf-8").write(s2)
        print(f"{new}  stage={stage}  {fn}")
    print("total", len(rows))


if __name__ == "__main__":
    main()
