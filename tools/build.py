#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建器：content/*.md  ->  web/

产物
  web/index.html                 首页（学习路线）
  web/lesson/<id>/index.html     每一课
  web/quiz/index.html            题库（随机抽题 + 错题本）
  web/glossary/index.html        术语总表（全站 :::term 自动汇总）
  web/search/index.html          全站搜索
  web/progress/index.html        进度看板
  web/cheatsheet/index.html      命令速查（content/_cheatsheet.md）
  web/data/{catalog,quiz,glossary,search}.json

设计原则
1. 单一数据源：目录、题库、术语、搜索索引全部从 content/*.md 解析生成，
   不存在"页面改了目录没改"的漂移。
2. 零依赖：只用标准库。
3. 块语法（写在 md 里，独立成行）：

   :::goal 一句话目标
   :::scene 场景标题
   :::term English | 中文
   :::pitfall 坑标题
   :::lab 动手标题
   :::quiz        （每行 "问题|答案"）
   :::check       （每行 "- 过关项"）
   :::note 旁注标题
   :::sandbox 预设名 | 提示语
   :::svg         （块内直接写 <svg>...</svg>）\n   :::fig <id> | 图注   （引用 web/fig/<id>.png，点击可放大）
"""
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
WEB = os.path.join(ROOT, "web")
LESSONS = os.path.join(WEB, "lesson")
DATA = os.path.join(WEB, "data")

STAGES = [
    (1, "阶段一 · Linux 与 Tcl 基础", "Linux 基础命令与文本处理 6 课 + Tcl 基础和编程 10 讲（均已上线）", "#2f7fd0"),
    (2, "阶段二 · 后端基本概念", "先懂芯片怎么造出来，再谈工具", "#18a07a"),
    (3, "阶段三 · Innovus 40nm 项目实操", "从一个空目录到能跑通的布局布线", "#c98a1e"),
    (4, "阶段四 · ICC2 32nm 项目", "换一套工具，把同一套方法论再走一遍", "#7a5cd6"),
    (5, "阶段五 · 28nm 全流程实战", "PR → PT → PV，像项目一样串起来", "#c05a7a"),
    (6, "阶段六 · STA 静态时序分析", "时序是后端的命，必须自己能算", "#b8860b"),
    (7, "阶段七 · 功耗分析与 RedHawk 实战", "芯片为什么会烧、会烫", "#a34a3a"),
    (8, "阶段八 · 实际工作经验分享", "别人踩过的坑，你别再踩", "#4a7a8c"),
    (9, "阶段九 · 求职与面试", "把会的东西讲清楚、卖出去", "#5a6b7a"),
]
STAGE_NAME = {s[0]: s[1] for s in STAGES}
STAGE_COLOR = {s[0]: s[3] for s in STAGES}
STAGE_SHORT = {s[0]: s[1].split("· ")[-1] for s in STAGES}

def asset_ver():
    """取 assets 目录下最新的 mtime 作为版本号，改了样式/脚本能立刻生效。"""
    d = os.path.join(WEB, "assets")
    try:
        v = max(os.path.getmtime(os.path.join(d, f)) for f in os.listdir(d))
    except (OSError, ValueError):
        v = 0
    return str(int(v))


def bust(html):
    v = asset_ver()
    for name in ("app.css", "app.js", "shell.js", "page.js", "tcl.js", "playground.js", "aiwidget.js", "logo.svg"):
        html = html.replace('/assets/' + name, '/assets/' + name + '?v=' + v)
    return html


NAV = [("/", "课程"), ("/playground/", "练习场"), ("/quiz/", "题库"), ("/exam/", "验收"), ("/glossary/", "术语"),
       ("/abbr/", "缩写"), ("/cheatsheet/", "速查"), ("/search/", "搜索"), ("/progress/", "进度")]

BLOCK_RE = re.compile(r"^:::([a-z]+)(?:[ \t]+(.*?))?[ \t]*\n(.*?)^:::[ \t]*$", re.S | re.M)


# ---------------------------------------------------------------- 基础工具
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def inline(t):
    """行内格式：**粗体**、`代码`、[文字](链接)"""
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def slug(s):
    s = re.sub(r"[^\w\u4e00-\u9fa5]+", "-", s.strip()).strip("-")
    return s.lower()[:40] or "ch"


def strip_md(s):
    """把 md 正文压成纯文本，用于术语释义与搜索索引。"""
    s = re.sub(r"^:::.*$", " ", s, flags=re.M)
    s = re.sub(r"^```[a-zA-Z]*$", " ", s, flags=re.M)
    s = re.sub(r"[#>*`]", " ", s)
    s = re.sub(r"\|", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def plain_line(s):
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s.strip()


def parse_front(src):
    m = re.match(r"^---\n(.*?)\n---\n", src, re.S)
    if not m:
        return {}, src
    meta = {}
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        meta[k.strip()] = v
    return meta, src[m.end():]


def nav_html(active=""):
    items = []
    for url, label in NAV:
        cls = ' class="on"' if url == active else ""
        items.append(f'<a{cls} href="{url}">{label}</a>')
    return "".join(items)


# ---------------------------------------------------------------- 块渲染
def render_term(arg, body):
    parts = [p.strip() for p in arg.split("|")]
    en = parts[0] if parts else ""
    zh = parts[1] if len(parts) > 1 else en
    txt = "\n".join(body).strip()
    return f"""<div class="term open">
  <div class="term-h"><span class="term-en">{inline(en)}</span><span class="term-zh">{inline(zh)}</span></div>
  <div class="term-b">{md(txt, inline_only=True)}</div>
</div>"""


def render_quiz(arg, body):
    rows = []
    for line in body:
        if "|" not in line:
            continue
        q, a = line.split("|", 1)
        rows.append(f"""<div class="q-item open">
  <div class="q-q"><span class="q-no"></span>{inline(q.strip())}</div>
  <div class="q-a">{inline(a.strip())}</div>
</div>""")
    if not rows:
        return ""
    return f'<div class="quiz"><div class="quiz-h">自测</div>{"".join(rows)}</div>'


def render_sandbox(arg):
    parts = [p.strip() for p in arg.split("|")]
    preset = parts[0] if parts else "basic"
    hint = parts[1] if len(parts) > 1 else "输入 help 看可用命令"
    return f"""<div class="sbx" data-preset="{esc(preset)}">
  <div class="sbx-h"><span class="sbx-dots"><i></i><i></i><i></i></span><b>模拟终端</b><span class="sbx-tip">{inline(hint)}</span><button class="sbx-rst" type="button">重置</button></div>
  <div class="sbx-body"><div class="sbx-out"></div>
    <div class="sbx-line"><span class="sbx-ps1">[autumn@eda ~]$</span><input class="sbx-in" spellcheck="false" autocomplete="off" autocapitalize="off" enterkeyhint="go" placeholder="输入命令，按回车运行" aria-label="模拟终端输入"></div>
  </div>
  <div class="sbx-f">这里跑的是浏览器里的模拟环境：命令、输出、报错都按真实 Linux 的行为写，练手够用；真机上的路径与权限另有差异。</div>
</div>"""


def render_block(name, arg, body):
    if name == "goal":
        return f'<div class="goal"><span>本章目标</span>{inline(arg or chr(10).join(body).strip())}</div>'
    if name == "scene":
        return f'<div class="scene"><div class="scene-h">工作场景 · {inline(arg)}</div><div class="scene-b">{md(chr(10).join(body))}</div></div>'
    if name == "term":
        return render_term(arg, body)
    if name == "pitfall":
        return f'<div class="pit"><div class="pit-h">常见坑 · {inline(arg)}</div><div class="pit-b">{md(chr(10).join(body))}</div></div>'
    if name == "lab":
        return f'<div class="lab"><div class="lab-h"><span class="lab-tag">动手</span>{inline(arg)}</div><div class="lab-b">{md(chr(10).join(body))}</div></div>'
    if name == "quiz":
        return render_quiz(arg, body)
    if name == "tip":
        return f'<div class="tip"><div class="tip-h">小技巧</div>{md(chr(10).join(body))}</div>'
    if name == "note":
        head = f'<div class="note-h">{inline(arg)}</div>' if arg else ""
        return f'<div class="note">{head}{md(chr(10).join(body))}</div>'
    if name == "check":
        items = "".join(f'<li>{inline(l.strip()[2:])}</li>' for l in body if l.strip().startswith("- "))
        return f'<div class="check"><div class="check-h">过关标准（都能做到才算学完）</div><ul>{items}</ul></div>'
    if name == "sandbox":
        return render_sandbox(arg)
    if name == "tclsh":
        return render_tclsh(arg, "")
    if name == "tclrun":
        return render_tclsh("", "\n".join(body).strip())
    if name == "fig":
        return render_fig(arg)
    if name == "svg":
        return '<div class="fig">' + "\n".join(body).strip() + "</div>"
    return md(chr(10).join(body))


def render_tclsh(arg, code):
    """Tcl 练习终端：browser 内置解释器。
       :::tclsh 提示语        —— 空终端自由练
       :::tclrun + 代码块体   —— 预置代码，一键运行"""
    hint = esc(arg or "在输入行敲 Tcl 命令，回车运行；输入 help 看支持的命令")
    codeattr = esc(code)
    hascode = " has-code" if code else ""
    return f"""<div class="tsbx{hascode}" data-code="{codeattr}">
  <div class="sbx-h"><span class="sbx-dots"><i></i><i></i><i></i></span><b>Tcl 练习台</b><span class="sbx-tip">{hint}</span><button class="sbx-rst" type="button">重置</button></div>
  {('<div class="tcl-code"><pre>' + esc(code) + '</pre><button class="tcl-go" type="button">▶ 运行这段代码</button></div>') if code else ''}
  <div class="sbx-body"><div class="sbx-out"></div>
    <div class="sbx-line"><span class="sbx-ps1">tclsh&gt;%</span><input class="sbx-in" spellcheck="false" autocomplete="off" autocapitalize="off" enterkeyhint="go" placeholder="输入 Tcl 命令，按回车运行" aria-label="Tcl 练习终端输入"></div>
  </div>
  <div class="sbx-f">这是浏览器内置的 Tcl 解释器（覆盖本课全部命令）：set / puts / expr / incr / append / 数组 / 列表 / if·while·foreach·for / proc 都能真跑。多行输入：先写上半句回车，解释器会等续行。</div>
</div>"""


FIG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def render_fig(arg):
    """:::fig <id> | 图注   —— 引用 web/fig/<id>，不写扩展名默认 .png

    早期配图全是截图，统一转成 .png；后来有插画类素材保留了 .jpg（转 png 只会更大），
    所以这里允许显式写扩展名：:::fig chip-finfet.jpg | 图注"""
    parts = [x.strip() for x in (arg or "").split("|")]
    fid = parts[0]
    cap = parts[1] if len(parts) > 1 else ""
    name = fid if fid.lower().endswith(FIG_EXT) else fid + ".png"
    if not os.path.exists(os.path.join(WEB, "fig", name)):
        print("WARN 配图不存在: web/fig/%s （:::fig %s）" % (name, fid))
    src = "/fig/" + name
    return (f'<figure class="fig-img"><a class="fig-a" href="{src}" data-fig="{esc(fid)}">'
            f'<img src="{src}" alt="{esc(cap)}" loading="lazy" decoding="async"></a>'
            f'<figcaption>{esc(cap)}</figcaption></figure>')


def render_code(lang, body):
    code = "\n".join(body)
    lines = []
    for ln in code.split("\n"):
        cls = ""
        s = ln.strip()
        if s.startswith("#") or s.startswith("//") or s.startswith(";") or s.startswith("*"):
            cls = "cmt"
        lines.append(f'<span class="ln {cls}">{esc(ln) or " "}</span>')
    return (f'<div class="code"><div class="code-h"><span class="code-lang">{esc(lang or "text")}</span>'
            f'<button class="copy" type="button">复制</button></div>'
            f'<pre><code>{"".join(lines)}</code></pre></div>')


def split_row(line):
    """按 | 切表格行，但跳过反引号代码段内的 |（例如 `a | b`、`ps -ef | grep x`）。
    也支持 \\| 转义。单元格里写管道符是 Tcl / shell 的日常需求，不切会整行错位。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells, buf, in_code, i = [], "", False, 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf += "|"
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
            buf += ch
            i += 1
            continue
        if ch == "|" and not in_code:
            cells.append(buf.strip())
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    cells.append(buf.strip())
    return cells


def md(src, inline_only=False):
    if inline_only:
        return "<p>" + "<br>".join(inline(l) for l in src.split("\n") if l.strip()) + "</p>"
    lines = src.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith(":::"):
            name = s[3:].strip()
            arg = ""
            if " " in name:
                name, arg = name.split(" ", 1)
            body, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            i += 1
            out.append(render_block(name.strip(), arg.strip(), body))
            continue
        if s.startswith("```"):
            lang = s[3:].strip()
            body, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            out.append(render_code(lang, body))
            continue
        if s.startswith("#### "):
            t = s[5:]
            m = re.match(r"^(.+?)\s*\{#([\w-]+)\}\s*$", t)
            if m:
                out.append(f'<h4 id="{m.group(2)}">{inline(m.group(1))}</h4>')
            else:
                out.append(f"<h4>{inline(t)}</h4>")
            i += 1
            continue
        if s.startswith("### "):
            t = s[4:]
            m = re.match(r"^(.+?)\s*\{#([\w-]+)\}\s*$", t)
            if m:
                out.append(f'<h3 id="{m.group(2)}">{inline(m.group(1))}</h3>')
            else:
                out.append(f"<h3>{inline(t)}</h3>")
            i += 1
            continue
        if s.startswith("## "):
            # 二级标题：课程正文里的 ## 已被 split_chapters 切走，
            # 这个分支服务于静态页（_abbr.md / _cheatsheet.md）。
            t = s[3:]
            m = re.match(r"^(.+?)\s*\{#([\w-]+)\}\s*$", t)
            if m:
                out.append(f'<h2 id="{m.group(2)}">{inline(m.group(1))}</h2>')
            else:
                out.append(f"<h2>{inline(t)}</h2>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            head = split_row(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_row(lines[i])
                if len(cells) != len(head):
                    print(f"WARN 表格列数不齐（表头 {len(head)} 列，本行 {len(cells)} 列）："
                          f"{lines[i].strip()[:80]}")
                if len(cells) < len(head):
                    cells += [""] * (len(head) - len(cells))
                rows.append(cells[:len(head)])
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
            continue
        if re.match(r"^[-*] ", s) or re.match(r"^\d+\. ", s):
            ordered = bool(re.match(r"^\d+\. ", s))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"^[-*] ", lines[i].strip()) or re.match(r"^\d+\. ", lines[i].strip())):
                items.append(re.sub(r"^([-*]|\d+\.) ", "", lines[i].strip()))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if s.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{md(chr(10).join(buf))}</blockquote>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,4} |:::|```|\||[-*] |\d+\. |> )", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        if not buf:
            # 兜底：任何未被上面分支识别的行（例如孤立的 | 开头行）也必须吃掉，
            # 否则 i 不前进会死循环。宁可渲染成普通段落，也不能卡住构建。
            buf.append(s)
            i += 1
        out.append("<p>" + " ".join(inline(x) for x in buf) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- 课程解析
def split_chapters(body):
    """按 ## 切章，返回 [(id, title, raw_md)]"""
    out, cur, buf = [], None, []
    for line in body.split("\n"):
        m = re.match(r"^## (.+?)(?:\s*\{#([\w-]+)\})?\s*$", line)
        if m:
            if cur:
                out.append((cur[0], cur[1], "\n".join(buf)))
            title = m.group(1).strip()
            cur = (m.group(2) or slug(title), title)
            buf = []
        else:
            buf.append(line)
    if cur:
        out.append((cur[0], cur[1], "\n".join(buf)))
    return out


def parse_lesson(path):
    fn = os.path.basename(path)[:-3]
    src = open(path, encoding="utf-8").read()
    meta, body = parse_front(src)
    meta.setdefault("id", fn)
    meta["chapters"] = []
    for cid, ctitle, raw in split_chapters(body):
        meta["chapters"].append({"id": cid, "title": ctitle, "raw": raw, "html": md(raw)})
    return meta


def load_all():
    lessons = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        L = parse_lesson(os.path.join(CONTENT, fn))
        if L.get("status", "live") == "draft":
            continue
        lessons.append(L)
    def _no_key(x):
        m = re.match(r"\d+", str(x.get("no", "")))
        return int(m.group()) if m else 9999
    lessons.sort(key=lambda x: (int(x.get("stage", 9)), _no_key(x)))
    return lessons


# ---------------------------------------------------------------- 数据抽取
def build_data(lessons):
    gloss, quiz, index = [], [], []
    for L in lessons:
        no, title, stage = str(L.get("no", "")), L.get("title", ""), int(L.get("stage", 0))
        for ch in L["chapters"]:
            raw = ch["raw"]
            ch["plain"] = strip_md(raw)
            # 术语
            for m in BLOCK_RE.finditer(raw):
                if m.group(1) != "term":
                    continue
                arg = (m.group(2) or "").split("|")
                en = plain_line(arg[0]) if arg else ""
                zh = plain_line(arg[1]) if len(arg) > 1 else en
                gloss.append({
                    "en": en, "zh": zh, "def": strip_md(m.group(3))[:400],
                    "lesson": L["id"], "lessonTitle": title, "no": no,
                    "stage": stage, "stageName": STAGE_SHORT.get(stage, ""),
                    "ch": ch["id"], "chTitle": ch["title"],
                })
            # 自测题
            for m in BLOCK_RE.finditer(raw):
                if m.group(1) != "quiz":
                    continue
                for line in m.group(3).split("\n"):
                    if "|" not in line:
                        continue
                    q, a = line.split("|", 1)
                    q, a = plain_line(q), a.strip()
                    a = re.sub(r"`([^`]+)`", r"\1", a)
                    a = re.sub(r"\*\*([^*]+)\*\*", r"\1", a)
                    if not q.strip():
                        continue
                    quiz.append({
                        "id": f"{L['id']}-{ch['id']}-{len(quiz)}",
                        "q": q.strip(), "a": a.strip(),
                        "lesson": L["id"], "lessonTitle": title, "no": no,
                        "stage": stage, "stageName": STAGE_SHORT.get(stage, ""),
                        "ch": ch["id"], "chTitle": ch["title"],
                    })
            index.append({
                "lesson": L["id"], "title": title, "no": no, "stage": stage,
                "stageName": STAGE_SHORT.get(stage, ""),
                "ch": ch["id"], "chTitle": ch["title"],
                "text": ch["plain"][:6000],
            })
    return gloss, quiz, index


# ---------------------------------------------------------------- 页面模板
HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{doctitle}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="/assets/logo.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/app.css">
</head>
<body data-page="{page}" data-lesson="{lesson}">
<header class="top">
  <a class="logo" href="/"><img class="mark" src="/assets/logo.svg" alt="IC 后端学院"><b>IC 后端学院</b><i>Backend Academy</i></a>
  <nav class="top-nav">{nav}</nav>
  <div class="top-right">{right}%%AUTHCHIP%%</div>
</header>"""

# 登录用户区（融入顶部导航右侧：头像 + 姓名 + 角色；管理员多一个审核入口）
AUTH_CHIP = """
<div id="userchip" class="userchip" hidden>
  <span class="uc-ava" id="uc-ava" aria-hidden="true"></span>
  <span class="uc-name" id="uc-name"></span>
  <span class="uc-role" id="uc-role" hidden>管理员</span>
  <a id="uc-admin" href="/admin" hidden>审核管理</a>
  <button id="uc-logout" type="button">退出</button>
</div>
<script>
(function(){
  fetch('/api/auth/me').then(function(r){return r.ok?r.json():Promise.reject();}).then(function(u){
    var el=document.getElementById('userchip');
    if(!el)return;
    el.hidden=false;
    var n=u.name||'学员';
    document.getElementById('uc-ava').textContent=n.charAt(0);
    document.getElementById('uc-name').textContent=n;
    if(u.role==='admin'){
      document.getElementById('uc-admin').hidden=false;
      document.getElementById('uc-role').hidden=false;
    }
    document.getElementById('uc-logout').addEventListener('click',function(){
      fetch('/api/auth/logout',{method:'POST'}).then(function(){location.href='/login';});
    });
  }).catch(function(){});
})();
</script>"""

PAGE = HEAD + """
<div class="layout">
  <aside class="toc" id="toc">
    <div class="toc-h">本课目录<span id="toc-count"></span></div>
    <nav id="toc-nav"></nav>
    <div class="toc-f">
      <a href="/">← 返回课程总览</a>
      <a href="/quiz/">去题库练这一课</a>
    </div>
  </aside>
  <main class="main">
    <div class="crumb"><a href="/">课程总览</a><span>/</span><a href="/#{stageAnchor}">{stageName}</a><span>/</span><b>{title}</b></div>
    <div class="hero">
      <div class="hero-no">{lessonNo}</div>
      <h1>{title}</h1>
      <p class="hero-en">{en}</p>
      <p class="hero-sum">{summary}</p>
      <div class="hero-meta">
        <span class="pill">约 {minutes} 分钟</span>
        <span class="pill">课表学时 {hours}</span>
        {tagPills}
      </div>
    </div>
    <article id="article">{article}</article>

    <section class="notes" id="notes">
      <div class="notes-h"><h3>我的笔记</h3><span id="note-state">只存在你自己账号下，换设备可恢复</span></div>
      <textarea id="note-box" placeholder="写下这一课你自己的话：哪个命令还没懂、哪份报告看不懂、下次要试什么。&#10;&#10;（建议不超过 8000 字）"></textarea>
      <div class="notes-f"><button id="note-save" class="pri" type="button">保存笔记</button><span id="note-msg"></span></div>
    </section>

    <div class="lesson-end">
      <div class="end-card">
        <h3>这一课学完了吗？</h3>
        <p>点一下标记整课完成。进度会自动同步到服务器，换电脑用同一个浏览器还能接着看。</p>
        <button id="btn-done" class="pri">标记本课完成</button>
        <div class="end-nav">{prevNext}</div>
      </div>
    </div>
  </main>
</div>
<script src="/assets/shell.js"></script>
<script src="/assets/tcl.js"></script>
<script src="/assets/app.js"></script>
<script src="/assets/aiwidget.js" defer></script>
</body>
</html>"""

SUB = HEAD + """
<main class="sub">
{body}
</main>
<script src="/assets/shell.js"></script>
<script src="/assets/tcl.js"></script>
<script src="/assets/page.js"></script>
<script src="/assets/playground.js"></script>
<script src="/assets/aiwidget.js" defer></script>
</body>
</html>"""

HOME = HEAD + """
<section class="home-hero">
  <div class="hh-in">
    <div class="hh-k">Digital Backend · 9 个阶段 · 课表 113 学时</div>
    <h1>把一块芯片<br>从代码变成版图</h1>
    <p>这门课写给<strong>完全没接触过芯片后端</strong>的人。每个概念先讲"它解决什么问题"，再讲工具怎么按；每个英文术语都给中文；每一行命令都写了注释和"删掉会怎样"。</p>
    <div class="hh-btns"><a class="pri" href="/lesson/{first}/">从第一课开始 →</a><a class="ghost" href="#plan">先看学习路线</a></div>
    <div class="hh-stats">{stats}</div>
  </div>
</section>

<section class="quick">
  <div class="qgrid">
    <a class="qcard" href="/playground/"><b>代码练习场</b><span>Linux 命令 + Tcl 代码 · 按课程顺序练 · 浏览器里直接跑</span></a>
    <a class="qcard" href="/quiz/"><b>题库</b><span>{nquiz} 道自测题 · 随机抽题 · 错题本</span></a>
    <a class="qcard" href="/glossary/"><b>术语表</b><span>{nterm} 条中英对照 · 按阶段筛选</span></a>
    <a class="qcard" href="/abbr/"><b>缩写解码</b><span>PR 里的三字母缩写 · 按场景分七组一页查</span></a>
    <a class="qcard" href="/cheatsheet/"><b>命令速查</b><span>Tcl / Linux 常用命令一页查</span></a>
    <a class="qcard" href="/progress/"><b>进度看板</b><span>哪一阶段欠多少、下一步学什么</span></a>
  </div>
</section>

<section class="plan" id="plan">
  <h2 class="sec-h">学习路线</h2>
  <p class="sec-p">按顺序学，不要跳。前一阶段是后一阶段的地基 —— 这也是很多人"看了很多教程还是不会做项目"的真正原因。</p>
  <div class="stages">{stages}</div>
</section>

<section class="faq" id="faq">
  <h2 class="sec-h">常见问题</h2>
  <div class="faq-grid">
    <div><h3>需要什么基础？</h3><p>会开机、会用浏览器就行。Linux 从"什么是终端"开始讲；数字电路的基本概念会在阶段二补。阶段一的 Linux 课自带浏览器内模拟终端，不装环境也能练。</p></div>
    <div><h3>要装什么软件？</h3><p>课程实验跑在一台 Linux 服务器上，浏览器里给命令、给解释、给预期输出；本机只需要一个 SSH 客户端。前面几个阶段的练习用页面里的模拟终端就能做完。</p></div>
    <div><h3>学完能做什么？</h3><p>能独立走完 综合 → 布局 → 时钟树 → 布线 → 时序签核 这条链路，看得懂每份报告，知道违例从哪来、怎么修。</p></div>
    <div><h3>为什么英文字母这么多？</h3><p>行业里就是这么叫的，改不了。所以每个术语第一次出现都给中英对照卡，点开有白话解释；全部术语还汇总在术语表里。</p></div>
  </div>
</section>

<footer class="foot">
  <p>IC 后端学院 · 课表 9 阶段 113 学时，已上线 {nhours} 学时 · 共 {nlesson} 课 {nchapter} 章</p>
</footer>
<script src="/assets/app.js"></script>
<script src="/assets/aiwidget.js" defer></script>
</body>
</html>"""


def build_lesson(L, idx, all_lessons):
    chs = L["chapters"]
    art = []
    for i, c in enumerate(chs):
        art.append(f"""<section class="ch" id="{c['id']}" data-ch="{c['id']}">
  <div class="ch-h"><span class="ch-n">{i+1:02d}</span><h2>{esc(c['title'])}</h2></div>
  {c['html']}
  <label class="ch-done"><input type="checkbox" data-mark="{c['id']}"><span>这一章我学完了</span></label>
</section>""")
    prev_next = ""
    if idx > 0:
        p = all_lessons[idx - 1]
        prev_next += f'<a class="nav-btn" href="/lesson/{p["id"]}/">← {esc(p["title"])}</a>'
    if idx + 1 < len(all_lessons):
        n = all_lessons[idx + 1]
        prev_next += f'<a class="nav-btn" href="/lesson/{n["id"]}/">{esc(n["title"])} →</a>'
    tags = L.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    tagPills = "".join(f'<span class="pill tag">{esc(t)}</span>' for t in tags)
    stage = int(L.get("stage", 0))
    html = PAGE.format(
        doctitle=f"{L.get('title','')} · {L.get('no','')} | IC 后端学院", title=L.get('title',''),
        desc=re.sub(r"[`*]", "", L.get("summary", "")),
        page="lesson", lesson=L["id"], nav=nav_html(),
        right='<div class="lp"><div class="lp-bar"><i id="lp-bar"></i></div><span id="lp-txt">0%</span></div>'
              '<button class="ghost" id="btn-reset" title="清空本机进度">重置</button>',
        stageAnchor=f"stage-{stage}", stageName=STAGE_NAME.get(stage, ""),
        lessonNo=L.get("no", ""), en=L.get("en", ""),
        summary=inline(L.get("summary", "")), minutes=L.get("minutes", 40),
        hours=L.get("hours", "—"), tagPills=tagPills, article="\n".join(art),
        prevNext=prev_next,
    ).replace("%%AUTHCHIP%%", AUTH_CHIP)
    out = os.path.join(LESSONS, L["id"])
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(bust(html))


def build_home(lessons, nquiz, nterm):
    by_stage = {}
    for L in lessons:
        by_stage.setdefault(int(L.get("stage", 0)), []).append(L)
    stages_html = []
    for num, name, desc, color in STAGES:
        items = by_stage.get(num, [])
        if not items:
            continue
        rows = "".join(
            f'<a class="lrow" href="/lesson/{L["id"]}/"><span class="lno">{esc(str(L.get("no","")))}</span>'
            f'<span class="lt">{esc(L.get("title",""))}<i>{esc(L.get("en",""))}</i></span>'
            f'<span class="lh">{esc(str(L.get("hours","")))} 学时</span><span class="lm">{esc(str(L.get("minutes",0)))} 分钟</span></a>'
            for L in items)
        stages_html.append(f"""<div class="stage" id="stage-{num}" style="--c:{color}">
  <div class="stage-l"><span class="stage-n">{num}</span></div>
  <div class="stage-r"><h3>{esc(name)}</h3><p>{esc(desc)}</p>
  <div class="lrows">{rows}</div></div>
</div>""")
    total_h = 0
    for L in lessons:
        try:
            total_h += float(L.get("hours", 0))
        except (TypeError, ValueError):
            pass
    nhours = ("%g" % total_h)
    nch = sum(len(L["chapters"]) for L in lessons)
    stats = (f'<div><b>{len(lessons)}</b><span>课程</span></div>'
             f'<div><b>{nch}</b><span>章节</span></div>'
             f'<div><b>{nhours}</b><span>已上线学时</span></div>')
    html = HOME.format(
        doctitle="IC 后端学院 · 零基础到能上手做项目", title="IC 后端学院",
        desc="面向零基础的 IC 数字后端课程：113 学时、9 个阶段，概念讲到能听懂，命令逐行注释，每一课都有可验收的实战。",
        page="home", lesson="home", nav=nav_html("/"),
        right='<a class="ghost" href="#plan">学习路线</a><a class="ghost" href="/progress/">我的进度</a>',
        first=lessons[0]["id"], stages="".join(stages_html), stats=stats,
        nquiz=nquiz, nterm=nterm, nlesson=len(lessons), nchapter=nch, nhours=nhours,
    ).replace("%%AUTHCHIP%%", AUTH_CHIP)
    open(os.path.join(WEB, "index.html"), "w", encoding="utf-8").write(bust(html))


# ---------------------------------------------------------------- 子页面
def subpage(slug, title, lead, body, active=""):
    html = SUB.format(
        doctitle=f"{title} | IC 后端学院", title=title, desc=lead, page=slug,
        lesson=slug, nav=nav_html(active or f"/{slug}/"),
        right='<a class="ghost" href="/">← 课程</a>',
        body=f'<div class="sub-h"><h1>{title}</h1><p>{lead}</p></div>' + body,
    ).replace("%%AUTHCHIP%%", AUTH_CHIP)
    d = os.path.join(WEB, slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(bust(html))


QUIZ_BODY = """
<div class="qbar">
  <div class="qbar-l">
    <button class="tab on" data-tab="draw" type="button">随机抽题</button>
    <button class="tab" data-tab="wrong" type="button">错题本 <i id="wrong-n">0</i></button>
    <button class="tab" data-tab="all" type="button">全部题目</button>
  </div>
  <div class="qbar-r">
    <select id="q-stage"><option value="">全部阶段</option></select>
    <button class="pri" id="q-start" type="button">开始 10 题</button>
  </div>
</div>
<div id="quiz-panel" class="qpanel"><p class="qempty">点右上角"开始 10 题"，随机抽 10 道；答完点"看答案"自评，答错的会自动进错题本。</p></div>
"""

GLOSS_BODY = """
<div class="gbar">
  <input id="g-q" type="search" placeholder="搜英文缩写或中文，例如 DRC / 时钟树 / 布线">
  <select id="g-stage"><option value="">全部阶段</option></select>
  <span id="g-n" class="gn"></span>
</div>
<div id="g-list" class="glist"></div>
"""

SEARCH_BODY = """
<div class="sbar">
  <input id="s-q" type="search" placeholder="搜课程内容，例如 setup hold / 拥塞 / tluplus / ECO">
  <span id="s-n" class="gn"></span>
</div>
<div id="s-hint" class="shint">输入关键词，回车。支持多个词（空格分隔，全部命中才显示）。</div>
<div id="s-list" class="slist"></div>
"""

EXAM_BODY = """
<div class="xnote">每个阶段一套<b>验收卷</b>：从该阶段全部课程的自测题里随机抽题（题多的阶段抽 20 道，题少的全出）。逐题自评计分，<b>80 分过关</b>。过关记录保存在本机浏览器，进度看板上会标"已验收"。建议：学完一个阶段立刻验收——不过关的题会告诉你该回哪一课复习。</div>
<div id="x-stages" class="xlist"></div>
<div id="x-panel" class="xpanel" hidden></div>
"""

PROGRESS_BODY = """
<div class="pwrap">
  <div class="pstats">
    <div><b id="p-pct">0%</b><span>总完成度</span></div>
    <div><b id="p-ch">0/0</b><span>已完成章节</span></div>
    <div class="pnext"><b id="p-next">—</b><span>下一课</span><i id="p-next-sub">—</i></div>
  </div>
  <div class="pbar"><i id="p-fill"></i></div>
  <div id="p-stages" class="pstages"></div>
  <div class="pnote">进度同时存在本机与服务器（匿名设备 ID），换设备用同一个浏览器可恢复；清浏览器数据会丢本机记录。</div>
</div>
"""


PLAYGROUND_BODY = """
<div class="pg-wrap">
  <div class="pg-modes">
    <button class="pg-mode on" data-mode="linux" type="button">Linux 命令练习</button>
    <button class="pg-mode" data-mode="tcl" type="button">Tcl 代码练习</button>
    <span class="pg-modes-hint">练习顺序 = 课程顺序：Linux 第 2–6 课 → Tcl 第 1–10 讲</span>
  </div>
  <div class="pg-toolbar">
    <select id="pg-example"><option value="">—— 按课程顺序选一组练习 ——</option></select>
    <button id="pg-run" class="pri" type="button">▶ 跑整段</button>
    <button id="pg-step" class="ghost" type="button">⏭ 下一条 (0/0)</button>
    <button id="pg-clear" class="ghost" type="button">清空终端</button>
    <button id="pg-reset" class="ghost" type="button">重置环境</button>
  </div>
  <div class="pg-grid">
    <div class="pg-editor">
      <div class="pg-eh" id="pg-eh">Linux 命令（一行一条，按顺序执行；# 开头是注释）</div>
      <textarea id="pg-code" spellcheck="false" autocomplete="off" wrap="off"></textarea>
    </div>
    <div class="pg-right">
      <div class="sbx pg-sbx" id="pg-term" data-preset="basic">
        <div class="sbx-h"><span class="sbx-dots"><i></i><i></i><i></i></span><b>交互终端</b><span class="sbx-tip">自己敲命令、回车就执行；↑↓ 历史、Tab 补全</span><button class="sbx-rst" type="button">重置</button></div>
        <div class="sbx-body"><div class="sbx-out"></div>
          <div class="sbx-line"><span class="sbx-ps1">[autumn@eda ~]$</span><input class="sbx-in" spellcheck="false" autocomplete="off" autocapitalize="off" enterkeyhint="go" placeholder="敲命令，回车执行（先敲 help 看支持哪些）" aria-label="模拟终端输入"></div>
        </div>
        <div class="sbx-f">和上面共用同一个环境：点「跑整段」等于把上面逐条敲进来，之后你可以接着改、接着试。想从头来就点「重置环境」。</div>
      </div>
      <div class="tsbx pg-tsbx" id="pg-tcl" style="display:none">
        <div class="sbx-h"><span class="sbx-dots"><i></i><i></i><i></i></span><b>Tcl 交互解释器</b><span class="sbx-tip">一行一执行；括号没闭合会自动等续行</span><button class="sbx-rst" type="button">重置</button></div>
        <div class="sbx-body"><div class="sbx-out"></div>
          <div class="sbx-line"><span class="sbx-ps1">tclsh&gt;%</span><input class="sbx-in" spellcheck="false" autocomplete="off" autocapitalize="off" enterkeyhint="go" placeholder="敲 Tcl 命令，回车执行" aria-label="Tcl 解释器输入"></div>
        </div>
        <div class="sbx-f">变量和 proc 都留在环境里：先 set 一个变量，下一行直接用它；多行结构（if / while / proc）写到一半回车会显示 ...&gt; 等续行。</div>
      </div>
      <div class="pg-stdin" id="pg-stdin-box" style="display:none">
        <div class="pg-eh">stdin 预输入（每行一条，供 gets stdin 读取）</div>
        <textarea id="pg-stdin" spellcheck="false" placeholder="例如脚本里有 gets stdin score，就在这里先写好 85"></textarea>
      </div>
    </div>
  </div>
  <div class="pg-note" id="pg-note"></div>
</div>
"""


def build_playground():
    subpage("playground", "代码练习场（Linux + Tcl）",
            "按课程顺序练：Linux 命令跑在模拟终端里，Tcl 代码直接执行。上面写、下面看输出，报错行为与真实环境一致。",
            PLAYGROUND_BODY)


def build_subpages(lessons, nquiz, nterm):
    subpage("quiz", "题库", f"{nquiz} 道自测题，按阶段筛选、随机抽题、自动记错题。", QUIZ_BODY)
    subpage("exam", "阶段验收", "学完一个阶段来验一验：随机抽题、80 分过关、进度看板留痕。", EXAM_BODY)
    subpage("glossary", "术语表", f"全站 {nterm} 条术语，英文原名 + 中文 + 白话解释 + 出处。", GLOSS_BODY)
    subpage("search", "搜索", "全站章节级搜索，命中后直接跳到对应小节。", SEARCH_BODY)
    subpage("progress", "学习进度", "按阶段看完成度，知道下一步该学哪一章。", PROGRESS_BODY)
    build_playground()
    build_cheatsheet()
    build_abbr()


def build_static(slug, filename, dft_title, dft_lead):
    """content/ 下划线开头的静态页（不进课程目录）→ web/<slug>/index.html"""
    p = os.path.join(CONTENT, filename)
    if not os.path.exists(p):
        return False
    meta, body = parse_front(open(p, encoding="utf-8").read())
    subpage(slug, meta.get("title", dft_title), meta.get("summary", dft_lead),
            f'<article class="art">{md(body)}</article>')
    return True


def build_cheatsheet():
    build_static("cheatsheet", "_cheatsheet.md", "命令速查", "常用命令一页查，按工具分组。")


def build_abbr():
    build_static("abbr", "_abbr.md", "缩写解码表", "PR 里的英文缩写，按场景分组一页查。")


def main():
    for d in (LESSONS, DATA):
        os.makedirs(d, exist_ok=True)
    lessons = load_all()
    gloss, quiz, index = build_data(lessons)
    for i, L in enumerate(lessons):
        build_lesson(L, i, lessons)
    build_home(lessons, len(quiz), len(gloss))
    build_subpages(lessons, len(quiz), len(gloss))

    cat = {
        "version": datetime.now().strftime("%Y.%m.%d"),
        "title": "IC 后端学院",
        "subtitle": "IC Backend Academy",
        "stages": [{"no": s[0], "name": s[1], "desc": s[2], "color": s[3]} for s in STAGES],
        "lessons": [{
            "id": L["id"], "no": str(L.get("no", "")), "stage": int(L.get("stage", 0)),
            "title": L.get("title", ""), "en": L.get("en", ""), "desc": L.get("summary", ""),
            "tags": L.get("tags", []), "status": "live", "minutes": int(L.get("minutes", 40)),
            "hours": str(L.get("hours", "")),
            "chapters": [{"id": c["id"], "title": c["title"]} for c in L["chapters"]],
        } for L in lessons],
        "counts": {"lessons": len(lessons), "chapters": sum(len(L["chapters"]) for L in lessons),
                   "quizzes": len(quiz), "terms": len(gloss)},
    }
    dump = lambda name, obj: open(os.path.join(DATA, name), "w", encoding="utf-8").write(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    dump("catalog.json", cat)
    dump("quiz.json", quiz)
    dump("glossary.json", gloss)
    dump("search.json", index)

    print(f"build ok: {len(lessons)} lessons / {cat['counts']['chapters']} chapters / "
          f"{len(quiz)} quizzes / {len(gloss)} terms")
    for L in lessons:
        print(f"  {str(L.get('no','')):<5} {L['id']:<26} {len(L['chapters'])} ch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
