#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成课程小节的「知识海报」配图。

做法分两步，原因是直接拿正文拼一句"画一张关于 X 的图"只会得到没信息量的插画：

    content/*.md ──按 ## 切小节──▶ 文本模型：先抽知识点，再编排成 2~4 页海报
                                      （每页固定版式：4 个分区 + 底部一句话 + 页码）
                                      │
                                      ▼
                               图像模型出图 ──视觉模型逐字核对────▶ 错字就重画
                                      │
                                      ▼
                          Pillow 压 jpeg ──▶ web/fig/ai/<课>-<节>-p<N>.jpg
                                      │
                                      ▼
                          tools/aifig_index.json（build.py 读它，插在小节标题下面）

用法：
    python tools/genfig.py --plan                     # 只列清单，不花钱
    python tools/genfig.py --dry-run --lesson 01-08   # 只出文案脚本，先审内容
    python tools/genfig.py --lesson 01-08             # 只做一课
    python tools/genfig.py                            # 补齐全站缺失
    python tools/genfig.py --force --lesson 01-08     # 强制重做
    python tools/genfig.py --audit --regen            # 全量复查，废图摘掉待重做

配置在 tools/aifig.config.json；密钥优先环境变量 AIFIG_API_KEY，其次 .aifig.key。
"""
import argparse
import base64
import hashlib
import io
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
WEB = os.path.join(ROOT, "web")
OUTDIR = os.path.join(WEB, "fig", "ai")
INDEX = os.path.join(ROOT, "tools", "aifig_index.json")
CFG_PATH = os.path.join(ROOT, "tools", "aifig.config.json")
KEY_PATH = os.path.join(ROOT, ".aifig.key")

PRINT_LOCK = threading.Lock()


def log(msg):
    with PRINT_LOCK:
        print(msg, flush=True)


# ---------------------------------------------------------------- 配置与鉴权
def load_cfg():
    with open(CFG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("base_url", "https://ai.feice.net/v1")
    cfg.setdefault("text_model", "gemini-3-flash")
    cfg.setdefault("image_model", "gpt-image-2.5")
    cfg.setdefault("image_size", "1536x1024")
    cfg.setdefault("out_width", 1400)
    cfg.setdefault("jpeg_quality", 86)
    cfg.setdefault("workers", 4)
    cfg.setdefault("retries", 3)
    cfg.setdefault("timeout", 300)
    cfg.setdefault("max_pages", 4)
    cfg.setdefault("min_pages", 1)
    cfg.setdefault("review", True)
    cfg.setdefault("review_model", cfg["text_model"])
    cfg.setdefault("review_retries", 2)
    cfg["base_url"] = cfg["base_url"].rstrip("/")
    return cfg


def api_key():
    k = os.environ.get("AIFIG_API_KEY", "").strip()
    if k:
        return k
    if os.path.exists(KEY_PATH):
        k = open(KEY_PATH, encoding="utf-8").read().strip()
        if k:
            return k
    raise SystemExit("缺少 API Key：设置环境变量 AIFIG_API_KEY，或写入 %s" % KEY_PATH)


def post_json(cfg, path, payload, timeout=None):
    """带重试的 JSON POST：429/5xx/网络抖动退避重试，4xx 直接报错。"""
    key = api_key()
    url = cfg["base_url"] + path
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last = None
    for attempt in range(cfg["retries"] + 1):
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", "Bearer " + key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout or cfg["timeout"]) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:400]
            last = "HTTP %s %s" % (e.code, body)
            if e.code not in (408, 409, 425, 429, 500, 502, 503, 504):
                raise RuntimeError(last)
        except Exception as e:                      # 超时、连接重置
            last = "%s: %s" % (type(e).__name__, e)
        if attempt < cfg["retries"]:
            wait = min(60, 5 * (2 ** attempt)) + random.random() * 2
            log("    ! %s，%.0fs 后重试（%d/%d）" % (last[:80], wait, attempt + 1, cfg["retries"]))
            time.sleep(wait)
    raise RuntimeError("重试耗尽：%s" % last)


def chat(cfg, system, user, max_tokens=2400, temperature=0.6):
    r = post_json(cfg, "/chat/completions", {
        "model": cfg["text_model"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }, timeout=240)
    return ((r.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


# ---------------------------------------------------------------- 扫描小节
def parse_front(src):
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", src, re.S)
    if not m:
        return meta, src
    for line in m.group(1).split("\n"):
        mm = re.match(r"^(\w+):\s*(.*)$", line)
        if mm:
            meta[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return meta, src[m.end():]


def split_sections(body):
    out, cur, buf = [], None, []
    for line in body.split("\n"):
        m = re.match(r"^## (.+?)(?:\s*\{#([\w-]+)\})?\s*$", line)
        if m:
            if cur:
                out.append((cur[0], cur[1], "\n".join(buf)))
            title = m.group(1).strip()
            aid = m.group(2) or re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "-", title.lower()).strip("-")[:40]
            cur = (aid, title)
            buf = []
        else:
            buf.append(line)
    if cur:
        out.append((cur[0], cur[1], "\n".join(buf)))
    return out


FENCE = re.compile(r"^```")


def body_text(raw):
    """给文本模型看的正文：去掉 ::: 块标记和代码块（代码不画进图，只浪费 token）。"""
    lines, out, in_fence = raw.split("\n"), [], False
    for ln in lines:
        if FENCE.match(ln.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = ln.strip()
        if not s or s.startswith(":::"):
            continue
        s = re.sub(r"^[-*]\s+", "", s)
        s = s.replace("**", "").replace("`", "").replace("|", " ")
        if re.match(r"^\|?\s*-{2,}", s):
            continue
        out.append(re.sub(r"\s{2,}", " ", s))
    return "\n".join(out).strip()


def scan(cfg):
    secs = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        meta, body = parse_front(open(os.path.join(CONTENT, fn), encoding="utf-8").read())
        if meta.get("status") == "draft":
            continue
        lid = meta.get("id") or fn[:-3]
        if lid in cfg.get("skip_lessons", []):
            continue
        for idx, (anchor, title, raw) in enumerate(split_sections(body), 1):
            if "%s#%s" % (lid, anchor) in cfg.get("skip_sections", []):
                continue
            manual = len(re.findall(r"^:::fig\s", raw, re.M))
            secs.append({
                "lesson": lid, "no": meta.get("no", ""), "lesson_title": meta.get("title", ""),
                "index": idx, "anchor": anchor, "title": title,
                "body": body_text(raw), "manual_figs": manual,
            })
    return secs


# ---------------------------------------------------------------- 文本模型：知识点 → 海报页
POINTS_SYS = """你是儿童科普图书的作者。给你课程里一个小节的正文，请把它拆成「核心知识点」，
每条都写清 6 件事——这是后面配图要挨个画到图上的，所以必须写得又准又短、小学生能看懂。

对每个知识点输出：
  name     知识点名字（≤8 字，儿童能读的名词，别用英文缩写）
  what     它是什么（≤14 字，一句话）
  use      它有什么用（≤14 字，讲清为什么要它）
  how      它是怎么工作的（≤14 字，动词开头，讲清运转方式）
  analogy  生活里的类比（≤14 字，用小孩熟悉的东西打比方，如「像给铅笔盒贴名字」）
  example  一个具体小例子（≤14 字，可以带数字/人名，如「名字=小明」）
  takeaway 一句话总结（≤16 字，口语，能当口诀念）
  icons    给 5 张卡片各配一个画面建议：{"what":"…","use":"…","how":"…","analogy":"…","example":"…"}，
           只描述画什么小图标或小场景，不要在画面描述里写文字

要求：
1. 覆盖正文里所有核心要点，一条都不能漏。**至少 2 条**；正文超过 400 字通常拆 3~5 条。
   一条知识点只装一个概念，不要把「是什么」和「怎么用」硬塞进同一条，也不要只给一条就交差。
2. 每条都必须能在图上放下，所以每句话都极短；不要从句、不要术语堆叠。术语第一次出现用括号写白话。
3. 不要出现代码、命令原文、英文缩写；需要提到就用中文说（如「查看文件内容的命令」）。
4. 全部用小学生口吻，别用"该""进行""完成"这类书面词。

严格输出 JSON，不要代码块、不要解释：
{"points":[{"name":"…","what":"…","use":"…","how":"…","analogy":"…","example":"…","takeaway":"…",
 "icons":{"what":"…","use":"…","how":"…","analogy":"…","example":"…"}}]}"""


def extract_points(cfg, sec):
    """抽知识点。模型偶尔只交一条就交差（正文明明有四个要点），所以条数不够就重问一次。"""
    body = sec["body"]
    if len(body) > 3000:
        body = body[:3000] + "\n……（后略）"
    user = ("课程：《%s》\n本节标题：%s\n\n本节正文：\n%s\n\n请拆出核心知识点并写清 6 要素。"
            % (sec["lesson_title"], sec["title"], body))
    need = 2 if len(body) > 180 else 1
    pts = []
    for attempt in range(3):
        extra = "" if attempt == 0 else (
            "\n\n注意：上一次%s，请把正文的要点拆全（至少 %d 条），并且 JSON 必须能解析。"
            % ("只拆了 %d 条太少" % len(pts) if pts else "输出格式不对", need))
        txt = chat(cfg, POINTS_SYS + extra, user, max_tokens=2600)
        try:
            pts = parse_points(txt)
        except Exception as e:
            log("    ~ 知识点解析失败（%s），再来一次" % str(e)[:60])
            pts = []
            continue
        if len(pts) >= need:
            return pts
        log("    ~ 只抽到 %d 条知识点，重问一次" % len(pts))
    if not pts:
        raise RuntimeError("知识点抽不出来")
    return pts


def parse_points(txt):
    s = re.sub(r"^```[a-zA-Z]*\s*", "", txt.strip())
    s = re.sub(r"\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        raise RuntimeError("知识点抽取无法解析：%s" % txt[:200].replace("\n", " "))
    try:
        data = json.loads(s[i:j + 1])
    except Exception as e:
        raise RuntimeError("知识点 JSON 坏了：%s" % e)
    pts = []
    for p in data.get("points") or []:
        if not isinstance(p, dict):
            continue
        ic = p.get("icons") or {}
        pts.append({
            "name": str(p.get("name", "")).strip(),
            "what": str(p.get("what", "")).strip(),
            "use": str(p.get("use", "")).strip(),
            "how": str(p.get("how", "")).strip(),
            "analogy": str(p.get("analogy", "")).strip(),
            "example": str(p.get("example", "")).strip(),
            "takeaway": str(p.get("takeaway", "")).strip(),
            "icons": {k: str(ic.get(k, "") or "").strip() for k in ("what", "use", "how", "analogy", "example")},
        })
    return [p for p in pts if p["name"] and p["what"]]


def build_pages(cfg, sec, pts):
    """知识点 → 海报页：先总览，之后每个知识点一页（5 张卡片 + 底部口诀）。

    这里由程序编排而不是让模型排，目的就是保证「每个知识点都有一页」，一条都不漏。
    知识点只有 1~2 条时不单独做总览页——两张大卡撑不满版面，反而显得空。"""
    pages = []
    title = re.sub(r"^\s*[0-9]+[.、]\s*", "", sec["title"] or "")[:12]   # 去掉「5. 」这类编号
    if len(pts) >= 3:
        ov = [{"h": p["name"], "t": (p["what"] or p["use"])[:12], "icon": p["icons"]["what"]} for p in pts[:5]]
        pages.append({
            "kind": "overview", "title": title, "blocks": ov,
            "footer": "看完这几张，这一节就懂了",
            "caption": "总览：这一节要弄明白的 %d 件事——%s。"
                       % (len(ov), "、".join(p["name"] for p in pts[:5])),
        })
    for p in pts:
        pages.append({
            "kind": "point",
            "title": p["name"][:10],
            "blocks": [
                {"h": "它是什么", "t": p["what"], "icon": p["icons"]["what"]},
                {"h": "有什么用", "t": p["use"], "icon": p["icons"]["use"]},
                {"h": "怎么工作", "t": p["how"], "icon": p["icons"]["how"]},
                {"h": "生活里像", "t": p["analogy"], "icon": p["icons"]["analogy"]},
                {"h": "举个例子", "t": p["example"], "icon": p["icons"]["example"]},
            ],
            "footer": p["takeaway"],
            "caption": "%s：%s（%s）" % (p["name"], p["what"], p["takeaway"]),
        })
    pages = pages[:cfg["max_pages"]]
    for i, p in enumerate(pages, 1):
        p["page"], p["total"] = i, len(pages)
    return pages


def make_pages(cfg, sec):
    return build_pages(cfg, sec, extract_points(cfg, sec))


def parse_pages(txt):
    s = re.sub(r"^```[a-zA-Z]*\s*", "", txt.strip())
    s = re.sub(r"\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return []
    try:
        d = json.loads(s[i:j + 1])
    except Exception:
        return []
    out = []
    for p in d.get("pages") or []:
        if not isinstance(p, dict):
            continue
        blocks = []
        for b in p.get("blocks") or []:
            if not isinstance(b, dict):
                continue
            h = str(b.get("h", "")).strip()
            t = str(b.get("t", "")).strip()
            if h and t:
                blocks.append({"h": h, "t": t, "icon": str(b.get("icon", "")).strip()})
        if not blocks:
            continue
        out.append({
            "kind": str(p.get("kind", "point")),
            "title": str(p.get("title", "")).strip(),
            "blocks": blocks[:5],
            "footer": str(p.get("footer", "")).strip(),
            "caption": str(p.get("caption", "")).strip(),
        })
    return out


# ---------------------------------------------------------------- 图像模型：知识海报
STYLE_HEAD = (
    "儿童科普知识海报（信息图），扁平卡通矢量风格：浅蓝天空背景、白色圆角大卡片承载内容、"
    "粗而柔和的深色描边、明亮可爱的配色（天蓝/草绿/暖黄/粉红/橙），"
    "每个分区配一个可爱的小图标或小场景，分区之间用粗箭头连接，留白充足、排版整齐、像儿童绘本里的知识页。"
)


def poster_prompt(cfg, sec, page, fix=""):
    """把一页文案拼成图像提示词。版式写死，模型只负责把字写对、把图标画好。"""
    n = len(page["blocks"])
    total = page.get("total", 1)
    if page["kind"] == "overview":
        layout = ("下方横向排 %d 张圆角小卡片，每张卡片顶部一个彩色小标题、下面半句提示、中间画对应小图标，"
                  "卡片之间用箭头连接表示这一节的学习顺序。" % n)
    elif n == 5:
        layout = ("下方排 %d 张圆角卡片：上排 3 张并排、下排 2 张居中并排（下排要和大卡片一样高，别留空）。"
                  "每张卡片顶部一个彩色小标题、下面一句话、中间画对应小图标。" % n)
    else:
        layout = ("下方按 2×2 或 4 列均匀排 %d 张圆角小卡片，每张卡片顶部一个彩色小标题、下面一句话、"
                  "中间画对应小图标；卡片按顺序用粗箭头连接。" % n)
    parts = [STYLE_HEAD,
             "顶部大标题（彩色手写体、大而醒目）：「%s」。" % page["title"],
             layout]
    for k, b in enumerate(page["blocks"], 1):
        parts.append("第%d张卡片：小标题「%s」，下面文字「%s」，配图 %s。" % (
            k, b["h"], b["t"], b["icon"] or "一个相关的小图标"))
    if page["footer"]:
        parts.append("底部一条彩色横条，写总结口诀：「%s」。" % page["footer"])
    if total > 1:
        parts.append("右下角小圆标签里写页码：「第 %d 页 / 共 %d 页」。" % (page["page"], total))
    if fix:
        parts.append(fix)
    parts.append("图上所有中文必须是规范简体中文，笔画完整清晰；"
                 "下面每一处文字都要一字不差地照抄上去，不许改写、润色、同义替换、缩写或合并句子；"
                 "不许出现英文、拼音、代码、乱码，也不要加我没要求的文字。")
    return " ".join(parts)


def draw(cfg, prompt):
    r = post_json(cfg, "/images/generations", {
        "model": cfg["image_model"],
        "prompt": prompt,
        "size": cfg["image_size"],
        "n": 1,
    })
    return base64.b64decode(r["data"][0]["b64_json"])


def save_jpeg(cfg, png_bytes, dst_base):
    try:
        from PIL import Image
    except ImportError:
        dst = dst_base + ".png"
        with open(dst, "wb") as f:
            f.write(png_bytes)
        return os.path.basename(dst), None, None
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    w = cfg["out_width"]
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    dst = dst_base + ".jpg"
    im.save(dst, "JPEG", quality=cfg["jpeg_quality"], optimize=True, progressive=True)
    return os.path.basename(dst), im.width, im.height


# ---------------------------------------------------------------- 视觉自检
REVIEW_SEM = threading.Semaphore(2)      # 视觉审核并发高了网关会返回空内容，压到 2

REVIEW_SYS = """你是印刷质检员。你会看到一张儿童知识海报，以及这张海报上「应该出现」的文字清单。

先逐字抄出图里的所有文字，再和清单比对，找出三类问题：
- missing：清单里有、图上确实没有的句子
- extra：图上多出来的整句说明文字（清单完全没提的）
- wrong：写错的字词、说反了的意思、被改写成另一个意思的句子

判定标准（宽松有底线，别把好图判死）：
1. 空格、标点、繁简、OCR 差异（例如「第 2 页 / 共 5 页」写成「第2页/共5页」、「它是什么」抄成「是什么」）→ 不算错。
2. 图上给的具体例子、数字、人名、物件名（比如「小明」「10」「我的书包」）→ 不算 extra，这是好事。
3. 同义改写（把「百变数据」写成「装啥都行」）、整句漏掉、术语错字（「目标」写成「自标」）→ 算 wrong。
4. 只报确实会误导读者的问题，宁少报不多报。

只输出 JSON：{"text":["抄到的文字"],"missing":["……"],"extra":["……"],"wrong":["期望→实际"]}"""


def expected_texts(page):
    t = [page["title"]]
    for b in page["blocks"]:
        t.append(b["h"])
        t.append(b["t"])
    if page["footer"]:
        t.append(page["footer"])
    if page.get("total", 1) > 1:
        t.append("第 %d 页 / 共 %d 页" % (page["page"], page["total"]))
    return [x for x in t if x]


def review_image(cfg, jpg_path, expects):
    """出图自检：整页文字逐字比对。审核自身失败时不阻塞出图，交给 --audit 兜底。"""
    b = base64.b64encode(open(jpg_path, "rb").read()).decode()
    lst = "\n".join("- " + x for x in expects)
    payload = {
        "model": cfg["review_model"],
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": REVIEW_SYS + "\n\n这张图上应该出现的文字：\n" + lst},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}},
        ]}],
        "temperature": 0,
        "max_tokens": 900,
    }
    txt = None
    with REVIEW_SEM:
        for _ in range(3):
            r = post_json(cfg, "/chat/completions", payload, timeout=150)
            txt = (r.get("choices") or [{}])[0].get("message", {}).get("content")
            if txt:
                break
            time.sleep(1.5)
    if not txt:
        return {"ok": True, "missing": [], "extra": [], "wrong": [], "unknown": True}
    return parse_review(txt, expects)


def _norm(s):
    """比对用的归一化：去掉空格和常见标点，避免「第 2 页 / 共 5 页」这种排版差异被当成错。"""
    return re.sub(r"[\s，。、：；！？,.:;!?·「」『』“”\"'（）()《》〈〉~～\-—/]+", "", str(s))


def parse_review(txt, expects=None):
    s = re.sub(r"^```[a-zA-Z]*\s*", "", txt.strip())
    s = re.sub(r"\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return {"ok": True, "missing": [], "extra": [], "wrong": [], "unknown": True}
    try:
        d = json.loads(s[i:j + 1])
    except Exception:
        return {"ok": True, "missing": [], "extra": [], "wrong": [], "unknown": True}

    def arr(k):
        v = d.get(k) or []
        return [str(x).strip() for x in v if str(x).strip()]

    miss, extra, wrong = arr("missing"), arr("extra"), arr("wrong")
    if expects:
        ex = [_norm(x) for x in expects]
        resp = [_norm(x) for x in arr("text")]
        # 清单里的句子如果在抄回的文本里能找到（归一化后互相包含），就不算漏
        miss = [m for m in miss if not any(_norm(m) and _norm(m) in r for r in resp)]
        # 多出来的，如果和清单里某句归一化后相同/包含，就不算多
        extra = [e for e in extra if not any(_norm(e) and (_norm(e) in x or x in _norm(e)) for x in ex)]
        # 「期望→实际」：归一化后相同、或互为子串（多是 OCR 少抄一个字，如 它是什么→是什么），都不算错
        keep = []
        for w in wrong:
            pair = re.split(r"\s*(?:→|->|=>)\s*", w)
            if len(pair) == 2:
                a, b = _norm(pair[0]), _norm(pair[1])
                if a == b or (a and b and (a in b or b in a)):
                    continue
            keep.append(w)
        wrong = keep
    return {"ok": not (miss or extra or wrong), "missing": miss, "extra": extra, "wrong": wrong}


# ---------------------------------------------------------------- 索引
def load_index():
    if os.path.exists(INDEX):
        try:
            return json.load(open(INDEX, encoding="utf-8"))
        except Exception:
            pass
    return {"version": 2, "items": {}}


def save_index(idx):
    tmp = INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, INDEX)


def sec_hash(cfg, sec):
    h = hashlib.sha1()
    for part in (sec["title"], sec["body"], cfg["image_model"], POINTS_SYS, str(cfg["max_pages"])):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- 生成一节
INDEX_CACHE = {}


def process_one(cfg, sec, force):
    key = "%s#%s" % (sec["lesson"], sec["anchor"])
    h = sec_hash(cfg, sec)
    old = INDEX_CACHE.get(key)
    if old and old.get("hash") == h and not force and old.get("layout") == "poster":
        if all(os.path.exists(os.path.join(WEB, f["file"])) for f in old.get("figs", [])):
            return key, None

    pages = make_pages(cfg, sec)
    figs = []
    for page in pages:
        base = "%s-%s-p%d" % (sec["lesson"], sec["anchor"], page["page"])
        expects = expected_texts(page)
        name = w = hgt = None
        fix, rev = "", None
        for attempt in range(cfg["review_retries"] + 1):
            png = draw(cfg, poster_prompt(cfg, sec, page, fix))
            name, w, hgt = save_jpeg(cfg, png, os.path.join(OUTDIR, base))
            if not cfg.get("review"):
                break
            rev = review_image(cfg, os.path.join(OUTDIR, name), expects)
            if rev["ok"]:
                break
            problems = "；".join(x for x in (
                "漏写 " + "/".join(rev["missing"]) if rev["missing"] else "",
                "多写 " + "/".join(rev["extra"]) if rev["extra"] else "",
                "写错 " + "/".join(rev["wrong"]) if rev["wrong"] else "") if x)
            if attempt < cfg["review_retries"]:
                log("    ~ %s 自检不过（%s）重画 %d/%d"
                    % (name, problems[:70], attempt + 1, cfg["review_retries"]))
                fix = ("上一版这里有问题（%s）。这一版必须一字不差地写这些字：%s。"
                       % (problems[:80], "、".join("「%s」" % x for x in expects)))
            else:
                log("    ! %s 重画 %d 次仍有问题（%s）" % (name, cfg["review_retries"], problems[:70]))
        figs.append({
            "file": "fig/ai/" + name, "w": w, "h": hgt,
            "caption": page["caption"] or (page["title"] + "：" + (page["footer"] or "")),
            "page": page["page"], "total": page["total"], "kind": page["kind"],
            "title": page["title"], "expected": expects,
            "checked": bool(rev and rev["ok"]),
        })
    rec = {
        "lesson": sec["lesson"], "no": sec["no"], "anchor": sec["anchor"], "title": sec["title"],
        "index": sec["index"], "hash": h, "model": cfg["image_model"], "layout": "poster",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "figs": figs,
    }
    return key, rec


def run_audit(cfg, idx, args):
    jobs = []
    for key, it in sorted(idx["items"].items()):
        if args.lesson and args.lesson not in key:
            continue
        for f in it.get("figs") or []:
            p = os.path.join(WEB, f["file"])
            expects = f.get("expected") or []
            if os.path.exists(p) and expects:
                jobs.append((key, f, p, expects))
    if not jobs:
        log("索引里没有可审的图（只审带 expected 的新版记录）")
        return 0
    log("待审 %d 张（审核模型 %s）" % (len(jobs), cfg["review_model"]))
    bad, done, bad_n = {}, 0, 0
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex:
        futs = {ex.submit(review_image, cfg, p, e): (key, f) for key, f, p, e in jobs}
        for fu in as_completed(futs):
            key, f = futs[fu]
            done += 1
            try:
                r = fu.result()
            except Exception as e:
                log("[%d/%d] %s 审核失败 %s" % (done, len(jobs), f["file"], str(e)[:80]))
                continue
            if not r["ok"]:
                bad[key] = True
                bad_n += 1
                log("[%d/%d] 废图 %s 漏=%s 多=%s 错=%s" % (
                    done, len(jobs), f["file"],
                    "/".join(r["missing"])[:40], "/".join(r["extra"])[:40], "/".join(r["wrong"])[:60]))
            elif done % 10 == 0:
                log("[%d/%d] …" % (done, len(jobs)))
    log("审核完成：%d 张，废图 %d 张（涉及 %d 节）" % (len(jobs), bad_n, len(bad)))
    if args.regen and bad:
        for k in bad:
            idx["items"].pop(k, None)
        save_index(idx)
        log("已摘掉 %d 节记录，下次运行会重画" % len(bad))
    return 0


def main():
    global INDEX_CACHE
    ap = argparse.ArgumentParser(description="批量生成课程知识海报配图")
    ap.add_argument("--plan", action="store_true", help="只列清单")
    ap.add_argument("--dry-run", action="store_true", help="只出文案脚本并打印，不出图")
    ap.add_argument("--lesson", default="", help="只处理 id 含该串的课")
    ap.add_argument("--only", default="", help="只处理 anchor 含该串的小节")
    ap.add_argument("--limit", type=int, default=0, help="最多处理几节")
    ap.add_argument("--force", action="store_true", help="忽略缓存强制重做")
    ap.add_argument("--include-manual", action="store_true", help="已有人工图的小节也做")
    ap.add_argument("--audit", action="store_true", help="只审已有图")
    ap.add_argument("--regen", action="store_true", help="配合 --audit：摘掉废图待重做")
    args = ap.parse_args()

    cfg = load_cfg()
    idx = load_index()
    INDEX_CACHE = idx["items"]

    if args.audit:
        return run_audit(cfg, idx, args)

    secs = scan(cfg)
    if not args.include_manual:
        skipped = [s for s in secs if s["manual_figs"]]
        secs = [s for s in secs if not s["manual_figs"]]
        if skipped:
            log("跳过 %d 个已有人工配图的小节（--include-manual 可覆盖）" % len(skipped))
    if args.lesson:
        secs = [s for s in secs if args.lesson in s["lesson"]]
    if args.only:
        secs = [s for s in secs if args.only in s["anchor"]]

    todo = []
    for s in secs:
        key = "%s#%s" % (s["lesson"], s["anchor"])
        old = idx["items"].get(key)
        fresh = (old and old.get("hash") == sec_hash(cfg, s) and not args.force
                 and old.get("layout") == "poster"
                 and all(os.path.exists(os.path.join(WEB, f["file"])) for f in old.get("figs", [])))
        if not fresh:
            todo.append(s)
    if args.limit:
        todo = todo[:args.limit]

    log("小节 %d 个，待做 %d 个（%s，%s，并发 %d）"
        % (len(secs), len(todo), cfg["image_model"], cfg["image_size"], cfg["workers"]))
    if args.plan:
        for s in todo:
            log("  %-24s #%-2d %s" % (s["lesson"], s["index"], s["title"]))
        return 0
    if args.dry_run:
        for s in todo:
            log("\n=== %s #%d %s" % (s["lesson"], s["index"], s["title"]))
            try:
                for p in make_pages(cfg, s):
                    log("  [第 %d/%d 页] %s" % (p["page"], p["total"], p["title"]))
                    for b in p["blocks"]:
                        log("      %s｜%s｜图标：%s" % (b["h"], b["t"], b["icon"][:30]))
                    if p["footer"]:
                        log("      总结：%s" % p["footer"])
                    log("      图注：%s" % p["caption"])
            except Exception as e:
                log("  FAIL %s" % e)
        return 0
    if not todo:
        log("没有待做的小节")
        return 0

    os.makedirs(OUTDIR, exist_ok=True)
    t0, done, fail = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex:
        futs = {ex.submit(process_one, cfg, s, args.force): s for s in todo}
        for fu in as_completed(futs):
            s = futs[fu]
            done += 1
            tag = "[%d/%d] %s#%s" % (done, len(todo), s["lesson"], s["anchor"])
            try:
                key, rec = fu.result()
                if rec is None:
                    log("%s 跳过（未变）" % tag)
                    continue
                idx["items"][key] = rec
                save_index(idx)
                INDEX_CACHE[key] = rec
                log("%s ok %d 页 · %s" % (tag, len(rec["figs"]), rec["figs"][0]["file"]))
            except Exception as e:
                fail.append((tag, str(e)))
                log("%s FAIL %s" % (tag, str(e)[:160]))
    log("完成：%d 节，失败 %d，用时 %.1f 分钟" % (len(todo) - len(fail), len(fail), (time.time() - t0) / 60))
    for tag, err in fail:
        log("  失败 %s：%s" % (tag, err[:160]))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
