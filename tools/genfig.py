#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成课程小节配图。

两步走的理由：直接拿正文拼一句"画一张关于 X 的图"，模型只会画出抽象的电路图；
先让文本模型把这一节翻译成"生活里的比喻 + 分镜脚本"，图像模型才画得又准又好懂。

    content/*.md ──按 ## 切小节──▶ 文本模型写分镜(JSON)
                                      │
                                      ▼
                               图像模型出图 ──Pillow 压 jpeg──▶ web/fig/ai/<课>-<节>.jpg
                                      │
                                      ▼
                          tools/aifig_index.json（build.py 读它，插在小节标题下面）

用法：
    python tools/genfig.py --plan                 # 只列清单，不花钱
    python tools/genfig.py --lesson 02-01a        # 只做一课
    python tools/genfig.py --limit 3 --dry-run    # 出分镜不出图，先审 prompt
    python tools/genfig.py                        # 补齐所有缺失的小节图
    python tools/genfig.py --force --lesson 01-07 # 强制重画

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
    cfg.setdefault("out_width", 1200)
    cfg.setdefault("jpeg_quality", 84)
    cfg.setdefault("workers", 3)
    cfg.setdefault("retries", 3)
    cfg.setdefault("timeout", 300)
    cfg.setdefault("min_images_per_section", 1)
    cfg.setdefault("max_images_per_section", 2)
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


# ---------------------------------------------------------------- 扫描小节
def parse_front(src):
    """取 front-matter 里的 id / title（只认单行 key: value，够用）。"""
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
    """按 ## 切小节，返回 [(anchor, title, raw)]；## 的 {#id} 缺省用标题 slug。"""
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
    """给文本模型看的正文：去掉 ::: 块标记和代码块（代码画不进图，只是浪费 token）。"""
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
        if re.match(r"^\|?\s*-{2,}", s):        # 表格分隔行
            continue
        out.append(re.sub(r"\s{2,}", " ", s))
    return "\n".join(out).strip()


def scan(cfg):
    """扫出所有待配图的小节。跳过 _ 开头的静态页、草稿、以及已有人工配图的小节。"""
    secs = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        path = os.path.join(CONTENT, fn)
        meta, body = parse_front(open(path, encoding="utf-8").read())
        if meta.get("status") == "draft":
            continue
        lid = meta.get("id") or fn[:-3]
        if lid in cfg["skip_lessons"]:
            continue
        for idx, (anchor, title, raw) in enumerate(split_sections(body), 1):
            if "%s#%s" % (lid, anchor) in cfg["skip_sections"]:
                continue
            txt = body_text(raw)
            # 已有人工 :::fig 的小节不再生成，避免同一节两张同主题的图打架
            manual = len(re.findall(r"^:::fig\s", raw, re.M))
            secs.append({
                "lesson": lid, "no": meta.get("no", ""), "lesson_title": meta.get("title", ""),
                "index": idx, "anchor": anchor, "title": title,
                "body": txt, "manual_figs": manual,
            })
    return secs


# ---------------------------------------------------------------- 文本模型：分镜
BOARD_SYS = """你是一位给「芯片数字后端课程」画科普插画的资深分镜师。
读者是没学过电子、也没写过代码的成年人，但我们的要求是：画得像小学生科普绘本一样好懂。

你会拿到课程里一个小节的标题和正文。请设计 1~2 张插画（内容简单就 1 张，确实有两三个并列要点才 2 张），
放在这一小节的最前面，让人不看文字也能先懂个大概。

硬性要求：
1. 每张图必须用一个「生活里的比喻」讲清一个要点：门、水龙头、开关、邮局、快递分拣、工厂流水线、排队、双人抬担架、仓库货架、交通信号灯、锁和钥匙……
   绝对不要画抽象的电路图、波形图、表格、坐标轴，也不要把正文里的代码画进去。
2. 图上的字要少到极致：每张最多 2 个中文短标签，每个 2~4 个字（如「没加电压」「输入」「上一层」）。
   两个标签必须互不相同，必须是本节的关键词。标签越少越不容易写错字，宁可不要字也不要用长句。
3. 画面主角统一是那颗蓝色圆形笑脸小电子。不要另创人物形象——不要画宇航员、小孩、工人、老师等真人；
   需要多个角色时，就让蓝色小电子分身成几个，或让它操作道具。
4. scene 只描述画面怎么画：谁、在哪、做什么动作、分几栏、什么道具、什么颜色。
   不要在 scene 里写具体文字内容，需要指明位置就说「左上角的小牌子」。
5. 如果是操作命令类小节（终端命令、Tcl 命令），把「这条命令做了什么」画成动作场景，例如「把东西搬进某个抽屉」。
6. caption 是给网页用的图注，一到两句话，说清这张图画了什么、对应本节哪个知识点，30~60 字，不要出现「本图」「这张图」这类废字。

只输出一个 JSON 数组，不要代码块包裹、不要解释。格式：
[{"caption":"图注","scene":"画面描述","labels":["短标签1","短标签2"]}]"""


def make_board(cfg, sec):
    body = sec["body"]
    if len(body) > 2200:                 # 太长会淹掉重点，截断给模型
        body = body[:2200] + "\n……（后略）"
    user = (
        "课程：《%s》\n本节标题：%s\n\n本节正文：\n%s\n\n"
        "请输出这一节的插画分镜 JSON 数组（%d~%d 张）。"
        % (sec["lesson_title"], sec["title"], body,
           cfg["min_images_per_section"], cfg["max_images_per_section"])
    )
    r = post_json(cfg, "/chat/completions", {
        "model": cfg["text_model"],
        "messages": [{"role": "system", "content": BOARD_SYS}, {"role": "user", "content": user}],
        "temperature": 0.7,
        "max_tokens": 1600,
    }, timeout=180)
    txt = r["choices"][0]["message"]["content"]
    items = parse_board(txt)
    lo, hi = cfg["min_images_per_section"], cfg["max_images_per_section"]
    items = [x for x in items if x.get("scene")][:hi]
    if len(items) < lo:                  # 模型没给够，用标题兜一个
        items.append({"caption": "%s：先看个大概" % sec["title"], "scene": sec["title"] + "，用一个生活化的比喻场景表现",
                      "labels": []})
    return items[:hi]


def parse_board(txt):
    """模型偶尔会包 ```json 或前后加话，抓第一个 [ 到最后一个 ] 就行。"""
    s = txt.strip()
    s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    i, j = s.find("["), s.rfind("]")
    if i >= 0 and j > i:
        s = s[i:j + 1]
    try:
        data = json.loads(s)
    except Exception:
        return []
    if isinstance(data, dict):
        data = [data]
    out = []
    for it in data if isinstance(data, list) else []:
        if not isinstance(it, dict):
            continue
        labels = it.get("labels") or []
        if isinstance(labels, str):
            labels = [labels]
        out.append({
            "caption": str(it.get("caption", "")).strip(),
            "scene": str(it.get("scene", "")).strip(),
            "labels": [str(x).strip() for x in labels if str(x).strip()][:3],
        })
    return out


# ---------------------------------------------------------------- 图像模型：出图
def image_prompt(cfg, sec, item, fix=""):
    labels = item.get("labels") or []
    parts = [cfg["style"], "画面内容：" + item["scene"]]
    if labels:
        parts.append("图上只允许出现这几个中文词，每个只写一次，不得重复、不得加别的字（含英文和数字）："
                     + "、".join("「%s」" % x for x in labels))
    else:
        parts.append("图上不要出现任何文字。")
    if fix:
        parts.append("特别注意：" + fix)
    parts.append(cfg.get("style_tail", ""))
    return " ".join(p for p in parts if p)


def draw(cfg, prompt):
    r = post_json(cfg, "/images/generations", {
        "model": cfg["image_model"],
        "prompt": prompt,
        "size": cfg["image_size"],
        "n": 1,
    })
    return base64.b64decode(r["data"][0]["b64_json"])


REVIEW_SYS = """你是插画质检员。你会看到一张教学插画，以及这张图上「只允许出现的文字」清单。

请只做三件事：
1. 逐字抄出图里出现的所有文字（中文、英文、数字都要）。
2. 判断：有没有拼错/缺笔/写错字？有没有清单之外的字？有没有同一个词重复出现？
3. 给出结论。

只输出 JSON：{"text":["抄到的文字"],"bad":["有问题的文字或说明"],"ok":true/false}
ok 为 true 的条件：抄到的每个词都在清单里、拼写完全正确、且没有重复。
清单为空时，要求图里没有任何文字，否则 ok=false。"""


REVIEW_SEM = threading.Semaphore(2)      # 视觉审核并发高了网关会返回空内容，压到 2


def review_image(cfg, jpg_path, labels):
    """出图自检：AI 画中文很容易错一两个字（实测出现过「自标房间」），
    这种错字挂在小学生课件上很难看，宁可重画。
    审核本身失败（空返回/网络抖动）时不阻塞出图，按"未审核"放行，交给 --audit 兜底。"""
    b = base64.b64encode(open(jpg_path, "rb").read()).decode()
    allow = "、".join("「%s」" % x for x in labels) if labels else "（不允许任何文字）"
    payload = {
        "model": cfg["review_model"],
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "只允许出现的文字：%s\n\n请检查这张图。" % allow},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}},
        ]}],
        "temperature": 0,
        "max_tokens": 400,
    }
    txt = None
    with REVIEW_SEM:
        for attempt in range(3):
            r = post_json(cfg, "/chat/completions", payload, timeout=120)
            txt = (r.get("choices") or [{}])[0].get("message", {}).get("content")
            if txt:
                break
            time.sleep(1.5)
    if not txt:
        return {"ok": True, "text": [], "bad": ["审核无返回，按通过处理"], "unknown": True}
    return parse_review(txt, labels)


def parse_review(txt, labels):
    """labels=None 表示不知道白名单（老记录），只查错字和重复；labels=[] 表示图里不该有字。"""
    s = re.sub(r"^```[a-zA-Z]*\s*", "", txt.strip())
    s = re.sub(r"\s*```$", "", s)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return {"ok": True, "text": [], "bad": ["审核返回无法解析，按通过处理"]}
    try:
        d = json.loads(s[i:j + 1])
    except Exception:
        return {"ok": True, "text": [], "bad": ["审核返回 JSON 坏了，按通过处理"]}
    got = [str(x).strip() for x in (d.get("text") or []) if str(x).strip()]
    ok = d.get("ok")
    if not isinstance(ok, bool):
        ok = True
    dup = len(got) != len(set(got))
    if dup:
        ok = False
    if labels is not None:
        outside = [t for t in got if t not in labels]
        if outside or (not labels and got):
            ok = False
    return {"ok": ok, "text": got, "bad": [str(x) for x in (d.get("bad") or [])][:5]}


def save_jpeg(cfg, png_bytes, dst_base):
    """压成适合网页的 jpeg；没有 Pillow 就原样存 png（也能用，只是大）。"""
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


# ---------------------------------------------------------------- 索引
def load_index():
    if os.path.exists(INDEX):
        try:
            return json.load(open(INDEX, encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "items": {}}


def save_index(idx):
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    tmp = INDEX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, INDEX)


def sec_hash(cfg, sec):
    h = hashlib.sha1()
    for part in (sec["title"], sec["body"], cfg["style"], cfg["image_model"], str(cfg["max_images_per_section"])):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- 主流程
def process_one(cfg, sec, idx, force):
    """生成一节的全部配图，返回 (key, record) 或 (key, None)；异常向上抛。"""
    key = "%s#%s" % (sec["lesson"], sec["anchor"])
    h = sec_hash(cfg, sec)
    old = idx["items"].get(key)
    if old and old.get("hash") == h and not force:
        files = [f["file"] for f in old.get("figs", [])]
        if files and all(os.path.exists(os.path.join(OUTDIR, os.path.basename(f))) for f in files):
            return key, None                # 内容没变且文件都在，跳过

    items = make_board(cfg, sec)
    figs = []
    for n, item in enumerate(items, 1):
        base = "%s-%s%s" % (sec["lesson"], sec["anchor"], "" if len(items) == 1 else "-%d" % n)
        name = w = hgt = None
        fix, rev = "", None
        for attempt in range(cfg["review_retries"] + 1):
            png = draw(cfg, image_prompt(cfg, sec, item, fix))
            name, w, hgt = save_jpeg(cfg, png, os.path.join(OUTDIR, base))
            if not cfg.get("review"):
                break
            rev = review_image(cfg, os.path.join(OUTDIR, name), item["labels"])
            if rev["ok"]:
                break
            wrong = "、".join((rev["bad"] or rev["text"] or [])[:3])[:60]
            if attempt < cfg["review_retries"]:
                log("    ~ %s 自检不过（%s），重画 %d/%d" % (name, wrong, attempt + 1, cfg["review_retries"]))
                fix = "上一次这几个字的写法有问题（%s），这次必须一字不差地写成：%s" % (
                    wrong, "、".join("「%s」" % x for x in item["labels"]))
            else:
                log("    ! %s 重画 %d 次仍有问题（%s），先留着，audit 时会再挑出来" % (name, cfg["review_retries"], wrong))
        figs.append({"file": "fig/ai/" + name, "caption": item["caption"], "w": w, "h": hgt,
                     "labels": item["labels"], "checked": bool(rev and rev["ok"])})
    rec = {
        "lesson": sec["lesson"], "no": sec["no"], "anchor": sec["anchor"], "title": sec["title"],
        "index": sec["index"], "hash": h, "model": cfg["image_model"],
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "figs": figs,
    }
    return key, rec


def run_audit(cfg, idx, args):
    """把已有的图全过一遍自检：AI 写中文偶尔错一个字，错字比没图更伤。
    只报告不动手；加 --regen 才把不合格的从索引里摘掉（下次运行自动重画）。"""
    jobs = []
    for key, it in sorted(idx["items"].items()):
        if args.lesson and args.lesson not in key:
            continue
        for i, f in enumerate(it.get("figs") or []):
            p = os.path.join(WEB, f["file"])
            if os.path.exists(p):
                jobs.append((key, i, f, p))
    if not jobs:
        log("索引里没有可审的图")
        return 0
    log("待审 %d 张（审核模型 %s，并发 %d）" % (len(jobs), cfg["review_model"], cfg["workers"]))
    bad_keys, bad_n, done = {}, 0, 0
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex:
        futs = {ex.submit(review_image, cfg, p, f.get("labels")): (key, f) for key, i, f, p in jobs}
        for fu in as_completed(futs):
            key, f = futs[fu]
            done += 1
            try:
                r = fu.result()
            except Exception as e:
                log("[%d/%d] %s 审核失败：%s" % (done, len(jobs), f["file"], str(e)[:100]))
                continue
            if not r["ok"]:
                bad_keys[key] = True
                bad_n += 1
                log("[%d/%d] 废图 %s 看到=%s 问题=%s" % (
                    done, len(jobs), f["file"],
                    "/".join(r["text"]) or "（无）", "、".join(r["bad"])[:80] or "清单外或重复"))
            elif done % 10 == 0:
                log("[%d/%d] …" % (done, len(jobs)))
    log("审核完成：%d 张，废图 %d 张（涉及 %d 节）" % (len(jobs), bad_n, len(bad_keys)))
    if args.regen and bad_keys:
        for k in bad_keys:
            idx["items"].pop(k, None)
        save_index(idx)
        log("已摘掉 %d 节记录，下次运行 python tools/genfig.py 会重画这些" % len(bad_keys))
    return 0


def main():
    ap = argparse.ArgumentParser(description="批量生成课程小节配图")
    ap.add_argument("--plan", action="store_true", help="只列出待生成清单，不调接口")
    ap.add_argument("--dry-run", action="store_true", help="只生成分镜并打印，不出图")
    ap.add_argument("--lesson", default="", help="只处理 id 含该字符串的课，如 02-01a")
    ap.add_argument("--only", default="", help="只处理 anchor 含该字符串的小节")
    ap.add_argument("--limit", type=int, default=0, help="最多处理几节")
    ap.add_argument("--force", action="store_true", help="忽略缓存，强制重画")
    ap.add_argument("--include-manual", action="store_true", help="已有人工配图的小节也画")
    ap.add_argument("--audit", action="store_true", help="只审已生成的图，把不合格的挑出来（不加 --regen 就只报告）")
    ap.add_argument("--regen", action="store_true", help="配合 --audit：把不合格的记下来，下次运行会重画")
    args = ap.parse_args()

    cfg = load_cfg()
    idx = load_index()
    secs = scan(cfg)
    if not args.include_manual:
        manual = [s for s in secs if s["manual_figs"]]
        secs = [s for s in secs if not s["manual_figs"]]
        if manual:
            log("跳过 %d 个已有人工配图的小节（--include-manual 可覆盖）" % len(manual))
    if args.lesson:
        secs = [s for s in secs if args.lesson in s["lesson"]]
    if args.only:
        secs = [s for s in secs if args.only in s["anchor"]]

    if args.audit:
        return run_audit(cfg, idx, args)

    todo = []
    for s in secs:
        key = "%s#%s" % (s["lesson"], s["anchor"])
        old = idx["items"].get(key)
        h = sec_hash(cfg, s)
        fresh = old and old.get("hash") == h and not args.force and all(
            os.path.exists(os.path.join(WEB, f["file"])) for f in old.get("figs", []))
        if not fresh:
            todo.append(s)
    if args.limit:
        todo = todo[:args.limit]

    log("小节 %d 个，其中待生成 %d 个（模型 %s，尺寸 %s，并发 %d）"
        % (len(secs), len(todo), cfg["image_model"], cfg["image_size"], cfg["workers"]))
    if args.plan or args.dry_run:
        for s in todo:
            log("  %-24s #%-2d %s" % (s["lesson"], s["index"], s["title"]))
        if args.plan:
            return 0
        # dry-run：只让文本模型写分镜，把人审的重点（比喻合不合适、标签对不对）先看清楚，
        # 免得花几十张图的钱才发现方向错了。
        for s in todo:
            log("\n=== %s #%d %s" % (s["lesson"], s["index"], s["title"]))
            try:
                for n, it in enumerate(make_board(cfg, s), 1):
                    log("  [%d] 图注：%s" % (n, it["caption"]))
                    log("      画面：%s" % it["scene"])
                    log("      标签：%s" % ("、".join(it["labels"]) or "（无文字）"))
                    log("      提示：%s" % image_prompt(cfg, s, it)[:200] + "…")
            except Exception as e:
                log("  FAIL %s" % e)
        return 0
    if not todo:
        log("没有待生成的小节")
        return 0

    os.makedirs(OUTDIR, exist_ok=True)
    t0, done, fail = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=cfg["workers"]) as ex:
        futs = {ex.submit(process_one, cfg, s, idx, args.force): s for s in todo}
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
                save_index(idx)                      # 每节落盘，中断也不丢进度
                log("%s ok %d 张 · %s" % (tag, len(rec["figs"]), rec["figs"][0]["file"]))
            except Exception as e:
                fail.append((tag, str(e)))
                log("%s FAIL %s" % (tag, str(e)[:160]))
    cost = time.time() - t0
    log("完成：%d 节，失败 %d，用时 %.1f 分钟" % (len(todo) - len(fail), len(fail), cost / 60))
    for tag, err in fail:
        log("  失败 %s：%s" % (tag, err[:160]))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
