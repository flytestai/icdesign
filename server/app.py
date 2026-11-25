#!/usr/bin/env python3
"""
IC 后端学院 · 后端服务
- 静态站点托管（web/）
- 课程目录 API
- 学习进度同步（匿名设备 ID）
- 课后笔记
- 用户注册 / 登录 / 管理员审核（未通过审核不能看课程内容）
"""
import base64
import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import quote
from contextlib import closing
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from PIL import Image
except ImportError:          # 服务器没装 Pillow 时图片压缩自动降级为原样存储
    Image = None

BASE = Path(os.environ.get("ICL_BASE", Path(__file__).resolve().parent))
WEB = BASE / "web"
DATA = BASE / "data"
DB = DATA / "app.db"
# 管理员上传/替换图片的持久目录：全量部署会原子切换 web/，存这里不受影响
MIRROR = DATA / "fig_mirror"
VERSION = "1.2.0"

DATA.mkdir(exist_ok=True)

app = FastAPI(title="IC 后端学院 API", version=VERSION, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=1024)

UID_RE = re.compile(r"^[A-Za-z0-9_\-]{4,40}$")
KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{1,48}$")
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")

SESSION_COOKIE = "ic_session"
SESSION_TTL = 7 * 24 * 3600  # 7 天

# 管理员内置账号
ADMIN_ACCOUNT = "weizhen"
ADMIN_PASSWORD = "wz729729"
ADMIN_PHONE = "19919930729"


def db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 120_000
    ).hex()


def init_db():
    with closing(db()) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS progress(
            uid TEXT NOT NULL, lesson TEXT NOT NULL, chapter TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 1, ts INTEGER NOT NULL,
            PRIMARY KEY(uid, lesson, chapter))""")
        c.execute("""CREATE TABLE IF NOT EXISTS notes(
            uid TEXT NOT NULL, lesson TEXT NOT NULL, body TEXT NOT NULL, ts INTEGER NOT NULL,
            PRIMARY KEY(uid, lesson))""")
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            account TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL DEFAULT '',
            pw_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sessions(
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS section_overrides(
            lesson TEXT NOT NULL, chapter TEXT NOT NULL,
            title TEXT, body TEXT, updated_at INTEGER NOT NULL,
            PRIMARY KEY(lesson, chapter))""")
        c.execute("""CREATE TABLE IF NOT EXISTS ai_settings(
            user_id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL DEFAULT 'openai',
            base_url TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT NOT NULL,
            updated_at INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ai_notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson TEXT NOT NULL DEFAULT '',
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            ts INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ai_chats(
            user_id INTEGER NOT NULL,
            lesson TEXT NOT NULL,
            messages TEXT NOT NULL,
            digest TEXT NOT NULL DEFAULT '',
            updated_at INTEGER NOT NULL,
            PRIMARY KEY(user_id, lesson))""")
        c.execute("""CREATE TABLE IF NOT EXISTS study_time(
            user_id INTEGER NOT NULL,
            lesson TEXT NOT NULL DEFAULT '',
            seconds INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY(user_id, lesson))""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_uids(
            user_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            ts INTEGER NOT NULL,
            PRIMARY KEY(user_id, uid))""")
        c.execute("""CREATE TABLE IF NOT EXISTS quiz_stats(
            user_id INTEGER PRIMARY KEY,
            answered INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            exam_passed INTEGER NOT NULL DEFAULT 0,
            best_exam INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_progress_uid ON progress(uid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_progress_lesson ON progress(lesson)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        # 种子管理员
        now = int(time.time())
        cur = c.execute("SELECT id FROM users WHERE account=?", (ADMIN_ACCOUNT,))
        if not cur.fetchone():
            salt = secrets.token_hex(16)
            c.execute(
                "INSERT INTO users(name,account,phone,pw_hash,salt,role,status,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                ("管理员", ADMIN_ACCOUNT, ADMIN_PHONE, hash_password(ADMIN_PASSWORD, salt), salt,
                 "admin", "approved", now, now))
        else:
            # 已有管理员但手机号为空时补录
            c.execute("UPDATE users SET phone=?, updated_at=? WHERE account=? AND (phone='' OR phone IS NULL)",
                      (ADMIN_PHONE, now, ADMIN_ACCOUNT))
        # 清理过期会话
        c.execute("DELETE FROM sessions WHERE expires < ?", (now,))
        c.commit()


init_db()


def check_uid(uid: str):
    if not UID_RE.match(uid or ""):
        raise HTTPException(status_code=400, detail="invalid uid")


# ================================================================ 认证
class RegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=20)
    phone: str = Field(..., max_length=16)
    password: str = Field(..., min_length=6, max_length=64)


class LoginIn(BaseModel):
    account: str = Field(..., max_length=32)
    password: str = Field(..., max_length=64)


class ReviewIn(BaseModel):
    uid: int
    action: str  # approve / reject / reset / delete


def current_user(request: Request) -> Optional[sqlite3.Row]:
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token or not re.match(r"^[a-f0-9]{64}$", token):
        return None
    with closing(db()) as c:
        row = c.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token=? AND s.expires>?",
            (token, int(time.time())),
        ).fetchone()
    return row


def start_session(response, user_id: int):
    token = secrets.token_hex(32)
    exp = int(time.time()) + SESSION_TTL
    with closing(db()) as c:
        c.execute("DELETE FROM sessions WHERE user_id=? OR expires<?", (user_id, int(time.time())))
        c.execute("INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)", (token, user_id, exp))
        c.commit()
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_TTL, path="/",
        httponly=True, samesite="lax",
    )


def user_public(u: sqlite3.Row) -> dict:
    return {
        "id": u["id"], "name": u["name"], "account": u["account"],
        "phone": u["phone"], "role": u["role"], "status": u["status"],
        "created_at": u["created_at"],
    }


@app.post("/api/auth/register")
def auth_register(r: RegisterIn):
    name = r.name.strip()
    phone = r.phone.strip()
    if not PHONE_RE.match(phone):
        raise HTTPException(400, "手机号格式不正确（仅支持中国大陆手机号）")
    if r.password != r.password.strip() or " " in r.password:
        raise HTTPException(400, "密码不能包含空格")
    now = int(time.time())
    salt = secrets.token_hex(16)
    with closing(db()) as c:
        if c.execute("SELECT id FROM users WHERE account=?", (phone,)).fetchone():
            raise HTTPException(400, "该手机号已注册，请直接登录或等待审核")
        c.execute(
            "INSERT INTO users(name,account,phone,pw_hash,salt,role,status,created_at,updated_at) "
            "VALUES(?,?,?,?,?,'user','pending',?,?)",
            (name, phone, phone, hash_password(r.password, salt), salt, now, now))
        c.commit()
    return {"ok": True, "message": "注册成功，请等待管理员审核通过后再登录使用"}


@app.post("/api/auth/login")
def auth_login(r: LoginIn, request: Request, response: Response):
    account = r.account.strip()
    with closing(db()) as c:
        # 账号或手机号均可登录（精确账号命中优先）
        u = c.execute(
            "SELECT * FROM users WHERE account=? OR phone=? "
            "ORDER BY CASE WHEN account=? THEN 0 ELSE 1 END",
            (account, account, account),
        ).fetchone()
    if not u:
        raise HTTPException(401, "账号不存在（请使用注册的手机号登录）")
    if hash_password(r.password, u["salt"]) != u["pw_hash"]:
        raise HTTPException(401, "密码不正确")
    start_session(response, u["id"])
    return {"ok": True, "status": u["status"], "role": u["role"], "name": u["name"]}


@app.post("/api/auth/logout")
def auth_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    if re.match(r"^[a-f0-9]{64}$", token):
        with closing(db()) as c:
            c.execute("DELETE FROM sessions WHERE token=?", (token,))
            c.commit()
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@app.get("/api/auth/me")
def auth_me(request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    return user_public(u)


class LinkUidIn(BaseModel):
    uid: str = Field(..., max_length=64)


@app.post("/api/auth/link-uid")
def auth_link_uid(r: LinkUidIn, request: Request):
    """把当前浏览器的设备 uid 登记到登录账号名下（排行榜按账号汇总进度用）。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    if not UID_RE.match(r.uid):
        raise HTTPException(400, "bad uid")
    with closing(db()) as c:
        c.execute("INSERT OR IGNORE INTO user_uids(user_id,uid,ts) VALUES(?,?,?)",
                  (u["id"], r.uid, int(time.time())))
        c.commit()
    return {"ok": True}


# ================================================================ 管理员
def require_admin(request: Request) -> sqlite3.Row:
    u = current_user(request)
    if not u or u["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")
    return u


@app.get("/api/admin/users")
def admin_users(request: Request):
    require_admin(request)
    with closing(db()) as c:
        rows = c.execute(
            "SELECT * FROM users ORDER BY "
            "CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, "
            "role='admin' DESC, created_at DESC").fetchall()
    return {"users": [user_public(r) for r in rows]}


@app.post("/api/admin/review")
def admin_review(r: ReviewIn, request: Request):
    admin = require_admin(request)
    with closing(db()) as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (r.uid,)).fetchone()
        if not row:
            raise HTTPException(404, "用户不存在")
        if row["role"] == "admin":
            raise HTTPException(400, "不能对管理员账号执行该操作")
        if r.action == "approve":
            status = "approved"
        elif r.action == "reject":
            status = "rejected"
        elif r.action == "reset":
            status = "pending"
        elif r.action == "delete":
            c.execute("DELETE FROM sessions WHERE user_id=?", (r.uid,))
            c.execute("DELETE FROM users WHERE id=?", (r.uid,))
            c.commit()
            return {"ok": True, "deleted": r.uid}
        else:
            raise HTTPException(400, "未知操作")
        c.execute("UPDATE users SET status=?, updated_at=? WHERE id=?",
                  (status, int(time.time()), r.uid))
        if status != "approved":
            c.execute("DELETE FROM sessions WHERE user_id=?", (r.uid,))
        c.commit()
    return {"ok": True, "uid": r.uid, "status": status, "by": admin["name"]}


# ================================================================ 管理员·课程内容编辑
# 设计：课程页是构建产物，编辑走"覆盖层"——管理员改的内容存进 section_overrides，
# lesson_page 出页时动态注入覆盖，所有人立即看到；重建/重新部署不会丢覆盖。
CH_RE = re.compile(r"^[\w-]{1,64}$")
FIG_RE = re.compile(r"^fig/[\w][\w\-./ ]*$")
FIG_EXT_OK = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MAX_SECTION_HTML = 300_000
MAX_FIG_BYTES = 12 * 1024 * 1024


class SectionIn(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = None


@app.get("/api/admin/sections/{lesson}")
def admin_get_sections(lesson: str, request: Request):
    require_admin(request)
    if not KEY_RE.match(lesson):
        raise HTTPException(400, "invalid lesson")
    with closing(db()) as c:
        rows = c.execute(
            "SELECT chapter,title,body,updated_at FROM section_overrides WHERE lesson=?",
            (lesson,)).fetchall()
    return {"overrides": {r["chapter"]: {"title": r["title"], "body": r["body"], "ts": r["updated_at"]}
                          for r in rows}}


@app.post("/api/admin/section/{lesson}/{chapter}")
def admin_set_section(lesson: str, chapter: str, r: SectionIn, request: Request):
    require_admin(request)
    if not KEY_RE.match(lesson) or not CH_RE.match(chapter):
        raise HTTPException(400, "invalid lesson/chapter")
    if not (WEB / "lesson" / lesson / "index.html").exists():
        raise HTTPException(404, "lesson not found")
    body = r.body
    n_conv = 0
    if body is not None:
        # 兜底：正文里任何外链/base64 图片一律转存到服务器本机，杜绝超链接引用
        body, n_conv = _localize_images(lesson, chapter, body)
        # 兜底：旧版折叠标记（"点击看解释"小字/看答案按钮）已改为默认展开，统一清掉
        body = re.sub(r'<i class="term-ico"[^>]*>[^<]*</i>', "", body)
        body = re.sub(r'<button class="q-show"[^>]*>[^<]*</button>', "", body)
    if body is not None and len(body) > MAX_SECTION_HTML:
        raise HTTPException(400, "小节内容过大（上限 30 万字符）")
    # 标题清洗：历史版本的编辑按钮曾挂在 h2 里，保存的标题可能带"✏️ 编辑"尾巴
    title = (r.title or "").strip() or None
    if title:
        title = re.sub(r"\s*✏️?\s*编辑\s*$", "", title).strip() or None
        title = title.replace("✏️ 编辑", "").replace("✏️编辑", "").replace("✏️", "").strip() or None
    body = body if (body is not None and body.strip()) else None
    with closing(db()) as c:
        c.execute(
            """INSERT INTO section_overrides(lesson,chapter,title,body,updated_at) VALUES(?,?,?,?,?)
               ON CONFLICT(lesson,chapter) DO UPDATE
               SET title=excluded.title, body=excluded.body, updated_at=excluded.updated_at""",
            (lesson, chapter, title, body, int(time.time())))
        c.commit()
    return {"ok": True, "lesson": lesson, "chapter": chapter, "images_localized": n_conv}


@app.delete("/api/admin/section/{lesson}/{chapter}")
def admin_del_section(lesson: str, chapter: str, request: Request):
    require_admin(request)
    if not KEY_RE.match(lesson) or not CH_RE.match(chapter):
        raise HTTPException(400, "invalid lesson/chapter")
    with closing(db()) as c:
        c.execute("DELETE FROM section_overrides WHERE lesson=? AND chapter=?", (lesson, chapter))
        c.commit()
    return {"ok": True}


@app.post("/api/admin/fig")
async def admin_fig(request: Request):
    """替换/新增 web/fig/ 下的图片：路径放 query（?path=fig/xxx.png），body 为图片原始字节。
    同名覆写 → 页面引用不变，/fig/ 本就是 no-cache，保存后刷新即见。"""
    require_admin(request)
    rel = request.query_params.get("path", "").strip().lstrip("/")
    if ".." in rel or not FIG_RE.match(rel):
        raise HTTPException(400, "非法图片路径")
    ext = os.path.splitext(rel)[1].lower()
    if ext not in FIG_EXT_OK:
        raise HTTPException(400, "不支持的图片格式（png/jpg/jpeg/webp/svg）")
    data = await request.body()
    if not data:
        raise HTTPException(400, "图片内容为空")
    if len(data) > MAX_FIG_BYTES:
        raise HTTPException(400, "图片超过 12MB")
    sub = rel[4:]                                   # 去掉 fig/ 前缀
    if ".." in sub:
        raise HTTPException(400, "非法图片路径")
    if sub.startswith("custom/"):
        # 粘贴/转存的新图 → 持久镜像（部署不受影响）
        target = MIRROR / sub
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    else:
        # 替换构建产物里的同名图：写 web（当前立即可见）+ 持久镜像（部署后仍生效）
        target = WEB / rel
        fig_root = os.path.realpath(WEB / "fig")
        real = os.path.realpath(target)
        if not real.startswith(fig_root + os.sep):
            raise HTTPException(400, "路径必须位于 fig/ 目录下")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        mtarget = MIRROR / sub
        mtarget.parent.mkdir(parents=True, exist_ok=True)
        mtarget.write_bytes(data)
    return {"ok": True, "path": rel, "size": len(data)}


# ---- 粘贴图片一律转存到服务器本机（杜绝外链/base64 引用） ----
PRIV_HOST_RE = re.compile(
    r"^(localhost|127\.|0\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|::1|\[::1)\S*$", re.I)
IMG_SRC_ATTR_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.I)
CT_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/svg+xml": "svg"}

# 图片压缩：PNG/大图 → WebP，屏幕宽上限 1400px。目标：贴图从 MB 级降到 ~100KB 级
MAX_IMG_W = 1400
COMPRESS_Q = 82


def _compress_image(data: bytes, ext: str) -> tuple:
    """压缩图片，返回 (bytes, ext)。SVG 原样返回；压缩失败原样返回。"""
    if ext == "svg" or Image is None:
        return data, ext
    try:
        im = Image.open(io.BytesIO(data))
        # 已经足够小且不是臃肿的 PNG → 原样
        if ext in ("jpg", "jpeg", "webp") and im.width <= MAX_IMG_W and len(data) < 300_000:
            return data, ext
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        if im.width > MAX_IMG_W:
            im = im.resize((MAX_IMG_W, round(im.height * MAX_IMG_W / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=COMPRESS_Q, method=6)
        out = buf.getvalue()
        if len(out) < len(data):
            return out, "webp"
        return data, ext
    except Exception:
        return data, ext


def _store_fig(data: bytes, ext: str, prefix: str = "paste") -> str:
    """压缩后按内容哈希落盘到持久镜像 fig_mirror/custom/（部署切换 web 不受影响）。
    重复图片自动复用同一文件。返回相对路径 fig/custom/xxx。"""
    data, ext = _compress_image(data, ext)
    h = hashlib.sha1(data).hexdigest()[:12]
    name = "%s-%s.%s" % (prefix, h, ext)
    target = MIRROR / "custom" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)
    return "fig/custom/" + name


def _fetch_ext_image(url: str) -> tuple:
    """下载外链图片，返回 (bytes, ext)。失败抛异常。"""
    host = urllib.parse.urlparse(url).hostname or ""
    if not host or PRIV_HOST_RE.match(host):
        raise ValueError("不允许的地址")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (icacademy-admin)"})
    with urllib.request.urlopen(req, timeout=12) as r:
        data = r.read(MAX_FIG_BYTES + 1)
        ct = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if not data or len(data) > MAX_FIG_BYTES:
        raise ValueError("图片为空或超过 12MB")
    if ct and ct in CT_EXT:
        ext = CT_EXT[ct]
    else:
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower().lstrip(".")
        if ext not in FIG_EXT_OK:
            raise ValueError("不是可识别的图片格式")
    return data, ext


def _localize_images(lesson: str, chapter: str, body: str) -> tuple:
    """把 body 里 <img src="http外链/data:base64"> 转存本机并替换。返回 (新body, 转换张数)。"""
    prefix = "%s-%s" % (lesson, chapter)
    cache = {}
    converted = 0

    def repl(m):
        nonlocal converted
        src = m.group(2)
        if src.startswith("/") or src.startswith("fig/"):
            return m.group(0)                      # 已是站内引用
        if src in cache:
            return m.group(1) + cache[src] + m.group(3)
        new_src = None
        try:
            if src.startswith("data:image/"):
                head, b64 = src.split(",", 1)
                mm = re.search(r"data:image/([a-z0-9+]+)", head, re.I)
                ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(
                    (mm.group(1).lower() if mm else "png"),
                    (mm.group(1).lower() if mm else "png"))
                data = base64.b64decode(b64, validate=False)
                if data and len(data) <= MAX_FIG_BYTES:
                    new_src = _store_fig(data, ext, prefix)
            elif re.match(r"^https?://", src, re.I):
                data, ext = _fetch_ext_image(src)
                new_src = _store_fig(data, ext, prefix)
        except Exception:
            new_src = None
        if new_src:
            cache[src] = new_src
            converted += 1
            return m.group(1) + new_src + m.group(3)
        return m.group(0)                          # 转存失败保留原样

    return IMG_SRC_ATTR_RE.sub(repl, body), converted


class FigFetchIn(BaseModel):
    url: str = Field(..., max_length=2000)


@app.post("/api/admin/fig-fetch")
def admin_fig_fetch(r: FigFetchIn, request: Request):
    """按 URL 抓取外链图片并存到服务器 fig/custom/，返回本地路径（编辑器粘贴外链图时用）。"""
    require_admin(request)
    url = r.url.strip()
    try:
        data, ext = _fetch_ext_image(url)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, "下载失败：%s" % str(e)[:80])
    rel = _store_fig(data, ext, "paste")
    return {"ok": True, "path": rel}


# ================================================================ AI 浮窗助教
# 每个用户配置自己的 AI 接口（OpenAI 兼容或 Anthropic），聊天由服务端代理转发：
# 浏览器不接触 API Key、也没有跨域问题；课程页自动附带课程上下文。
AI_PROVIDERS = {
    "openai": {"name": "OpenAI 兼容", "base": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "anthropic": {"name": "Anthropic Claude", "base": "https://api.anthropic.com", "model": "claude-sonnet-4-20250514"},
}


class AISettingsIn(BaseModel):
    provider: str = Field("openai", max_length=24)
    base_url: str = Field(..., max_length=300)
    api_key: str = Field("", max_length=300)
    model: str = Field(..., max_length=120)


class AIModelsIn(BaseModel):
    provider: str = Field("openai", max_length=24)
    base_url: str = Field(..., max_length=300)
    api_key: str = Field("", max_length=300)


class AIChatIn(BaseModel):
    messages: List[dict] = Field(..., max_length=40)
    lesson: Optional[str] = None
    digest: Optional[str] = Field(None, max_length=2000)   # 早期对话压缩摘要


class AIChatSaveIn(BaseModel):
    """保存某节课的对话（按用户 + 课程隔离持久化）。"""
    lesson: str = Field("", max_length=64)
    messages: List[dict] = Field(default_factory=list, max_length=200)


# 上下文压缩阈值：超过就保留摘要 + 最近若干轮
CHAT_KEEP_TURNS = 12          # 压缩后保留的最近消息条数（约 6 轮）
CHAT_MSG_MAX = 200            # 单课最多存多少条消息


def _ai_settings_of(user_id: int) -> Optional[sqlite3.Row]:
    with closing(db()) as c:
        return c.execute("SELECT * FROM ai_settings WHERE user_id=?", (user_id,)).fetchone()


def _safe_ai_host(base_url: str) -> str:
    """SSRF 防护：AI 接口地址不允许指向内网。本地测试可用 ICL_ALLOW_PRIVATE_AI=1 放开。"""
    host = urllib.parse.urlparse(base_url).hostname or ""
    if not host:
        raise HTTPException(400, "接口地址无效")
    if PRIV_HOST_RE.match(host) and not os.environ.get("ICL_ALLOW_PRIVATE_AI"):
        raise HTTPException(400, "接口地址不允许指向内网/本机")
    return host


@app.get("/api/ai/settings")
def ai_get_settings(request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    row = _ai_settings_of(u["id"])
    if not row:
        return {"configured": False, "providers": AI_PROVIDERS}
    key = row["api_key"]
    return {
        "configured": True, "provider": row["provider"], "base_url": row["base_url"],
        "model": row["model"],
        "api_key_masked": (key[:4] + "****" + key[-4:]) if len(key) > 8 else "****",
        "providers": AI_PROVIDERS,
    }


@app.post("/api/ai/settings")
def ai_set_settings(r: AISettingsIn, request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    if r.provider not in ("openai", "anthropic"):
        raise HTTPException(400, "provider 仅支持 openai / anthropic")
    base = r.base_url.strip().rstrip("/")
    if not re.match(r"^https?://", base, re.I):
        raise HTTPException(400, "接口地址必须以 http(s):// 开头")
    _safe_ai_host(base)
    model = r.model.strip()
    if not model:
        raise HTTPException(400, "请填写模型名称")
    key = r.api_key.strip()
    old = _ai_settings_of(u["id"])
    if not key and old:                      # 不填 key 表示沿用旧 key
        key = old["api_key"]
    if not key:
        raise HTTPException(400, "请填写 API Key")
    now = int(time.time())
    with closing(db()) as c:
        c.execute(
            """INSERT INTO ai_settings(user_id,provider,base_url,api_key,model,updated_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET provider=excluded.provider,
               base_url=excluded.base_url, api_key=excluded.api_key,
               model=excluded.model, updated_at=excluded.updated_at""",
            (u["id"], r.provider, base, key, model, now))
        c.commit()
    return {"ok": True}


@app.delete("/api/ai/settings")
def ai_del_settings(request: Request):
    """删除当前用户的大模型配置。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    with closing(db()) as c:
        cur = c.execute("DELETE FROM ai_settings WHERE user_id=?", (u["id"],))
        c.commit()
    return {"ok": True, "deleted": cur.rowcount}


@app.post("/api/ai/models")
def ai_models(r: AIModelsIn, request: Request):
    """代理拉取厂商模型列表：OpenAI 兼容走 GET {base}/models，Anthropic 走 GET {base}/v1/models。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    if r.provider not in ("openai", "anthropic"):
        raise HTTPException(400, "provider 仅支持 openai / anthropic")
    base = r.base_url.strip().rstrip("/")
    if not re.match(r"^https?://", base, re.I):
        raise HTTPException(400, "接口地址必须以 http(s):// 开头")
    _safe_ai_host(base)
    key = r.api_key.strip()
    if not key:
        old = _ai_settings_of(u["id"])
        if old:
            key = old["api_key"]             # key 留空时沿用已保存的 key
    if not key:
        raise HTTPException(400, "请先填写 API Key")
    if r.provider == "anthropic":
        url = re.sub(r"/v1/?$", "", base) + "/v1/models"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    else:
        url = base + "/models"
        headers = {"Authorization": "Bearer " + key}
    headers["User-Agent"] = "icacademy/1.2"
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        try:
            msg = (e.read().decode("utf-8", "ignore") or "").strip()[:200]
        except Exception:
            msg = str(e.reason or "")
        raise HTTPException(502, "拉取模型列表失败 HTTP %s：%s" % (e.code, msg))
    except Exception as e:
        raise HTTPException(502, "拉取模型列表失败：%s" % str(e)[:120])
    ids = []
    for it in (data.get("data") or data.get("models") or []):
        mid = (it.get("id") or it.get("name")) if isinstance(it, dict) else str(it)
        if mid:
            ids.append(str(mid))
    ids = sorted(set(ids))
    if not ids:
        raise HTTPException(502, "接口返回了空模型列表，请确认地址和 Key 是否正确")
    return {"models": ids}


class AINoteIn(BaseModel):
    question: str = Field(..., max_length=4000)
    answer: str = Field(..., max_length=12000)
    lesson: str = Field("", max_length=64)


@app.post("/api/ai/notes")
def ai_note_add(r: AINoteIn, request: Request):
    """保存一条 AI 问答为笔记。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    lesson = r.lesson.strip()
    if lesson and not KEY_RE.match(lesson):
        lesson = ""
    q = r.question.strip()
    a = r.answer.strip()
    if not q or not a:
        raise HTTPException(400, "问答内容为空")
    now = int(time.time())
    with closing(db()) as c:
        cur = c.execute(
            "INSERT INTO ai_notes(user_id,lesson,question,answer,ts) VALUES(?,?,?,?,?)",
            (u["id"], lesson, q[:4000], a[:12000], now))
        c.commit()
    return {"ok": True, "id": cur.lastrowid}


@app.get("/api/ai/notes")
def ai_note_list(request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    with closing(db()) as c:
        rows = c.execute(
            "SELECT id,lesson,question,answer,ts FROM ai_notes WHERE user_id=? "
            "ORDER BY id DESC LIMIT 200", (u["id"],)).fetchall()
    return {"notes": [
        {"id": r["id"], "lesson": r["lesson"], "question": r["question"],
         "answer": r["answer"], "ts": r["ts"]} for r in rows]}


@app.delete("/api/ai/notes/{note_id}")
def ai_note_del(note_id: int, request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    with closing(db()) as c:
        cur = c.execute("DELETE FROM ai_notes WHERE id=? AND user_id=?", (note_id, u["id"]))
        c.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "笔记不存在")
    return {"ok": True}


class QuizStatIn(BaseModel):
    answered: int = Field(0, ge=0, le=100000)   # 累计答过多少题（去重后的题数）
    correct: int = Field(0, ge=0, le=100000)    # 其中答对多少
    exam_passed: int = Field(0, ge=0, le=100)   # 通过验收的阶段数
    best_exam: int = Field(0, ge=0, le=100)     # 验收最高分


@app.post("/api/quiz-stats")
def quiz_stats_save(r: QuizStatIn, request: Request):
    """刷题进度上报（题数只增不减，避免清本地存储后倒退）。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    now = int(time.time())
    with closing(db()) as c:
        old = c.execute("SELECT answered,correct,exam_passed,best_exam FROM quiz_stats WHERE user_id=?",
                        (u["id"],)).fetchone()
        if old:
            answered = max(old["answered"], r.answered)
            correct = min(answered, max(old["correct"], r.correct))
            exam_passed = max(old["exam_passed"], r.exam_passed)
            best_exam = max(old["best_exam"], r.best_exam)
        else:
            answered, correct = r.answered, min(r.answered, r.correct)
            exam_passed, best_exam = r.exam_passed, r.best_exam
        c.execute(
            "INSERT INTO quiz_stats(user_id,answered,correct,exam_passed,best_exam,updated_at) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET answered=excluded.answered, "
            "correct=excluded.correct, exam_passed=excluded.exam_passed, "
            "best_exam=excluded.best_exam, updated_at=excluded.updated_at",
            (u["id"], answered, correct, exam_passed, best_exam, now))
        c.commit()
    return {"ok": True, "answered": answered, "correct": correct,
            "exam_passed": exam_passed, "best_exam": best_exam}


@app.get("/api/quiz-stats")
def quiz_stats_get(request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    with closing(db()) as c:
        r = c.execute("SELECT * FROM quiz_stats WHERE user_id=?", (u["id"],)).fetchone()
    if not r:
        return {"answered": 0, "correct": 0, "exam_passed": 0, "best_exam": 0}
    return {"answered": r["answered"], "correct": r["correct"],
            "exam_passed": r["exam_passed"], "best_exam": r["best_exam"]}


class StudyTimeIn(BaseModel):
    lesson: str = Field("", max_length=64)
    seconds: int = Field(..., ge=0, le=7200)      # 单次上报：最多 2 小时


@app.post("/api/study-time")
def study_time_add(r: StudyTimeIn, request: Request):
    """课程页停留时间上报（按用户 + 课程累计），用于排行榜的“学习时长”项。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    if not r.seconds:
        return {"ok": True, "added": 0}
    lesson = (r.lesson or "").strip()
    if lesson and not KEY_RE.match(lesson):
        raise HTTPException(400, "bad lesson")
    now = int(time.time())
    with closing(db()) as c:
        c.execute(
            "INSERT INTO study_time(user_id,lesson,seconds,updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id,lesson) DO UPDATE SET seconds=seconds+excluded.seconds, "
            "updated_at=excluded.updated_at",
            (u["id"], lesson, int(r.seconds), now))
        c.commit()
    return {"ok": True, "added": int(r.seconds)}


@app.get("/api/study-time")
def study_time_mine(request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    with closing(db()) as c:
        rows = c.execute("SELECT lesson,seconds FROM study_time WHERE user_id=?", (u["id"],)).fetchall()
    total = sum(r["seconds"] for r in rows)
    return {"total": total, "by_lesson": {r["lesson"]: r["seconds"] for r in rows}}


@app.get("/api/leaderboard")
def leaderboard(request: Request):
    """排行榜：综合分 = 进度分 70% + 时长分 30%。

    进度分：已完成章节数 / 全站章节总数
    时长分：学习秒数 / 全站最长学习秒数（无记录则为 0）
    只统计 approved / admin 用户，不暴露账号与手机号。
    """
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    total_chapters = _total_chapters()
    total_quizzes = _total_quizzes()
    total_stages = _total_stages()
    with closing(db()) as c:
        users = c.execute(
            "SELECT id,name,role FROM users WHERE status='approved' OR role='admin'").fetchall()
        # 按 (uid, lesson, chapter) 去重，避免重复上报
        prog = c.execute(
            "SELECT DISTINCT uid, lesson, chapter FROM progress WHERE done=1").fetchall()
        times = c.execute("SELECT user_id, SUM(seconds) s FROM study_time GROUP BY user_id").fetchall()
        links = c.execute("SELECT user_id,uid FROM user_uids").fetchall()
        qstats = c.execute("SELECT * FROM quiz_stats").fetchall()
    uid_map = {}
    for l in links:
        uid_map.setdefault(l["user_id"], set()).add(l["uid"])
    # 每个 uid 的已完成章节集合（跨设备合并到账号时按章节去重）
    prog_by_uid = {}
    for p in prog:
        prog_by_uid.setdefault(p["uid"], set()).add(p["lesson"] + "|" + p["chapter"])
    time_by_user = {t["user_id"]: t["s"] for t in times}
    quiz_by_user = {r["user_id"]: r for r in qstats}

    rows = []
    for us in users:
        uids = uid_map.get(us["id"], set())
        chapters = set()
        for x in uids:
            chapters |= prog_by_uid.get(x, set())
        done = len(chapters)
        secs = time_by_user.get(us["id"], 0)
        qs = quiz_by_user.get(us["id"])
        answered = qs["answered"] if qs else 0
        correct = qs["correct"] if qs else 0
        exam_passed = qs["exam_passed"] if qs else 0
        rows.append({
            "name": us["name"], "role": us["role"],
            "done": min(done, total_chapters), "total": total_chapters,
            "seconds": secs,
            "answered": answered, "correct": correct,
            "total_quizzes": total_quizzes,
            "exam_passed": exam_passed, "total_stages": total_stages,
        })
    max_secs = max([r["seconds"] for r in rows] or [0]) or 1
    for r in rows:
        # 三个维度各自归一化到 0~100
        p_score = (r["done"] / r["total"] * 100) if r["total"] else 0
        q_score = (r["answered"] / r["total_quizzes"] * 100) if r["total_quizzes"] else 0
        t_score = (r["seconds"] / max_secs * 100) if max_secs else 0
        r["progress_pct"] = round(p_score, 1)
        r["quiz_pct"] = round(q_score, 1)
        r["time_pct"] = round(t_score, 1)
        # 权重：进度 50% + 刷题 30% + 时长 20%
        r["score"] = round(p_score * 0.5 + q_score * 0.3 + t_score * 0.2, 1)
    rows.sort(key=lambda x: (-x["score"], -x["done"], -x["answered"], -x["seconds"], x["name"]))
    me = u["name"]
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["is_me"] = (r["name"] == me)
    return {"rows": rows, "me": me, "total_chapters": total_chapters,
            "total_quizzes": total_quizzes, "total_stages": total_stages,
            "weights": {"progress": 0.5, "quiz": 0.3, "time": 0.2}}


def _total_quizzes() -> int:
    """题库总题数（web/data/quiz.json）。"""
    p = WEB / "data" / "quiz.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return len(data if isinstance(data, list) else (data.get("quizzes") or []))
    except Exception:
        return 0


def _total_stages() -> int:
    """阶段总数（catalog.json 的 stages）。"""
    p = WEB / "data" / "catalog.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return len(data.get("stages") or [])
    except Exception:
        return 0


def _total_chapters() -> int:
    """全站章节总数（读 web/data/catalog.json）。读不到则回退 0。"""
    p = WEB / "data" / "catalog.json"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return sum(len(L.get("chapters") or []) for L in (data.get("lessons") or []))
    except Exception:
        return 0


def _strip_html(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s{2,}", " ", html).strip()


def _lesson_context(lesson_id: str, limit: int = 6000) -> str:
    if not KEY_RE.match(lesson_id):
        return ""
    p = WEB / "lesson" / lesson_id / "index.html"
    if not p.exists():
        return ""
    try:
        return _strip_html(p.read_text(encoding="utf-8"))[:limit]
    except Exception:
        return ""


def _chat_key(lesson: str) -> str:
    """课程页用 lesson id；非课程页统一存在空 lesson（全局会话）。"""
    lesson = (lesson or "").strip()
    return lesson if lesson and KEY_RE.match(lesson) else ""


def _clean_msgs(raw) -> List[dict]:
    out = []
    for m in raw or []:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = str(m.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            out.append({"role": role, "content": content[:8000]})
    return out


def _compress(msgs: List[dict], digest: str) -> tuple:
    """上下文超长时压缩：保留最近 N 条，更早的折成一句摘要（不调用大模型，纯文本提炼）。"""
    if len(msgs) <= CHAT_KEEP_TURNS:
        return msgs, digest
    cut = len(msgs) - CHAT_KEEP_TURNS
    old, keep = msgs[:cut], msgs[cut:]
    # 提炼被丢弃部分的问题要点，接到 digest 末尾
    qs = [m["content"].replace("\n", " ")[:60] for m in old if m["role"] == "user"]
    if qs:
        add = "；".join(qs[-12:])
        digest = (digest + "；" + add) if digest else add
        digest = digest[-1200:]
    return keep, digest


@app.get("/api/ai/chat/history")
def ai_chat_get(lesson: str = "", request: Request = None):
    """读取该用户在这节课的历史对话（刷新后可恢复）。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    key = _chat_key(lesson)
    with closing(db()) as c:
        row = c.execute("SELECT messages, digest, updated_at FROM ai_chats WHERE user_id=? AND lesson=?",
                        (u["id"], key)).fetchone()
    if not row:
        return {"messages": [], "digest": "", "updated_at": 0, "compressed": False}
    try:
        msgs = json.loads(row["messages"])
    except Exception:
        msgs = []
    return {"messages": msgs, "digest": row["digest"], "updated_at": row["updated_at"],
            "compressed": bool(row["digest"])}


@app.post("/api/ai/chat/history")
def ai_chat_save(r: AIChatSaveIn, request: Request):
    """保存对话（按用户 + 课程隔离）。超长自动压缩：保留最近若干轮 + 早期要点摘要。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    key = _chat_key(r.lesson)
    msgs = _clean_msgs(r.messages)[-CHAT_MSG_MAX:]
    with closing(db()) as c:
        old = c.execute("SELECT digest FROM ai_chats WHERE user_id=? AND lesson=?",
                        (u["id"], key)).fetchone()
        digest = old["digest"] if old else ""
        msgs, digest = _compress(msgs, digest)
        c.execute(
            "INSERT INTO ai_chats(user_id,lesson,messages,digest,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(user_id,lesson) DO UPDATE SET messages=excluded.messages, "
            "digest=excluded.digest, updated_at=excluded.updated_at",
            (u["id"], key, json.dumps(msgs, ensure_ascii=False), digest, int(time.time())))
        c.commit()
    return {"ok": True, "count": len(msgs), "compressed": bool(digest)}


@app.delete("/api/ai/chat/history")
def ai_chat_clear(lesson: str = "", request: Request = None):
    """清空该课的对话（用户主动清空）。"""
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    key = _chat_key(lesson)
    with closing(db()) as c:
        cur = c.execute("DELETE FROM ai_chats WHERE user_id=? AND lesson=?", (u["id"], key))
        c.commit()
    return {"ok": True, "cleared": cur.rowcount}


@app.post("/api/ai/chat/reply")
def ai_chat(r: AIChatIn, request: Request):
    u = current_user(request)
    if not u:
        raise HTTPException(401, "not logged in")
    if u["status"] != "approved" and u["role"] != "admin":
        raise HTTPException(403, "pending review")
    row = _ai_settings_of(u["id"])
    if not row:
        raise HTTPException(400, "NO_AI_CONFIG")
    # 组装消息：课程上下文（system）+ 早期摘要（system）+ 最近若干轮对话
    msgs = [m for m in r.messages if m.get("role") in ("user", "assistant") and str(m.get("content", "")).strip()]
    msgs = msgs[-10:]
    sys_parts = []
    if r.lesson:
        ctx = _lesson_context(r.lesson)
        if ctx:
            sys_parts.append(
                "你是「IC 后端学院」的课程助教。下面是用户正在学习的课程《%s》的页面内容，"
                "回答时优先依据这份内容，用中文、面向初学者讲清楚；课程里没讲到的可以补充通识。\n\n"
                "---- 课程内容开始 ----\n%s\n---- 课程内容结束 ----" % (r.lesson, ctx))
    if r.digest:
        sys_parts.append("用户在这节课早前问过（供你保持上下文连贯，不必复述）：" + r.digest)
    if sys_parts:
        msgs = [{"role": "system", "content": "\n\n".join(sys_parts)}] + msgs
    if not msgs:
        raise HTTPException(400, "消息为空")
    try:
        if row["provider"] == "anthropic":
            sys_txt = "\n".join(m["content"] for m in msgs if m["role"] == "system")
            chat_msgs = [{"role": m["role"], "content": m["content"]} for m in msgs if m["role"] != "system"]
            payload = {"model": row["model"], "max_tokens": 2000, "system": sys_txt, "messages": chat_msgs}
            url = row["base_url"] + "/v1/messages"
            headers = {"x-api-key": row["api_key"], "anthropic-version": "2023-06-01",
                       "Content-Type": "application/json"}
        else:
            payload = {"model": row["model"], "messages": msgs, "temperature": 0.5, "max_tokens": 2000}
            url = row["base_url"] + "/chat/completions"
            headers = {"Authorization": "Bearer " + row["api_key"], "Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                     method="POST", headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        if row["provider"] == "anthropic":
            reply = "".join(b.get("text", "") for b in (data.get("content") or []) if isinstance(b, dict))
        else:
            reply = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        if not reply:
            raise ValueError("AI 返回为空")
        return {"ok": True, "reply": reply}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise HTTPException(502, "AI 接口返回 %s：%s" % (e.code, body or "无详情"))
    except Exception as e:
        raise HTTPException(502, "调用 AI 接口失败：%s" % str(e)[:200])


@app.post("/api/admin/fig-upload")
async def admin_fig_upload(request: Request):
    """粘贴图上传：服务端压缩（PNG→WebP、限宽 1400px）后按内容哈希落盘，
    返回本地路径。前端不用再指定文件名，保存的正文天然引用压缩后的小图。"""
    require_admin(request)
    data = await request.body()
    if not data:
        raise HTTPException(400, "图片内容为空")
    if len(data) > MAX_FIG_BYTES:
        raise HTTPException(400, "图片超过 12MB")
    head = data[:16]
    if head.startswith(b"\x89PNG"):
        ext = "png"
    elif head.startswith(b"\xff\xd8"):
        ext = "jpg"
    elif head[:4] == b"RIFF" and data[8:12] == b"WEBP":
        ext = "webp"
    elif b"<svg" in data[:1024].lower():
        ext = "svg"
    else:
        raise HTTPException(400, "不是可识别的图片格式")
    rel = _store_fig(data, ext, "paste")
    return {"ok": True, "path": rel}


# ================================================================ 原有 API
class Item(BaseModel):
    lesson: str = Field(..., max_length=48)
    chapter: str = Field(..., max_length=48)
    done: bool = True


class ProgressIn(BaseModel):
    uid: str
    items: List[Item]


class NoteIn(BaseModel):
    uid: str
    lesson: str
    body: str = Field("", max_length=8000)


@app.get("/api/health")
def health():
    return {"ok": True, "version": VERSION, "time": int(time.time())}


@app.get("/api/catalog")
def catalog():
    p = WEB / "data" / "catalog.json"
    if not p.exists():
        raise HTTPException(404, "catalog not built")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")),
                        headers={"Cache-Control": "public, max-age=60"})


@app.get("/api/progress/{uid}")
def get_progress(uid: str):
    check_uid(uid)
    with closing(db()) as c:
        rows = c.execute(
            "SELECT lesson, chapter, done, ts FROM progress WHERE uid=? AND done=1", (uid,)
        ).fetchall()
    return {"uid": uid, "items": [dict(r) for r in rows]}


@app.post("/api/progress")
def post_progress(p: ProgressIn):
    check_uid(p.uid)
    if len(p.items) > 200:
        raise HTTPException(400, "too many items")
    now = int(time.time())
    with closing(db()) as c:
        for it in p.items:
            if not (KEY_RE.match(it.lesson) and KEY_RE.match(it.chapter)):
                continue
            if it.done:
                c.execute(
                    "INSERT INTO progress(uid,lesson,chapter,done,ts) VALUES(?,?,?,1,?) "
                    "ON CONFLICT(uid,lesson,chapter) DO UPDATE SET done=1, ts=excluded.ts",
                    (p.uid, it.lesson, it.chapter, now))
            else:
                c.execute("DELETE FROM progress WHERE uid=? AND lesson=? AND chapter=?",
                          (p.uid, it.lesson, it.chapter))
        c.commit()
    return {"ok": True, "saved": len(p.items)}


@app.delete("/api/progress/{uid}")
def reset_progress(uid: str):
    check_uid(uid)
    with closing(db()) as c:
        c.execute("DELETE FROM progress WHERE uid=?", (uid,))
        c.commit()
    return {"ok": True}


@app.delete("/api/progress/{uid}/{lesson}")
def reset_progress_lesson(uid: str, lesson: str):
    """清除单课学习进度（进度为滚动自动记录，清除后重新滚动会再次记录）。"""
    check_uid(uid)
    if not KEY_RE.match(lesson):
        raise HTTPException(400, "bad lesson")
    with closing(db()) as c:
        c.execute("DELETE FROM progress WHERE uid=? AND lesson=?", (uid, lesson))
        c.commit()
    return {"ok": True}


@app.get("/api/notes/{uid}/{lesson}")
def get_note(uid: str, lesson: str):
    check_uid(uid)
    with closing(db()) as c:
        r = c.execute("SELECT body, ts FROM notes WHERE uid=? AND lesson=?", (uid, lesson)).fetchone()
    return {"body": r["body"] if r else "", "ts": r["ts"] if r else 0}


@app.put("/api/notes")
def put_note(n: NoteIn):
    check_uid(n.uid)
    with closing(db()) as c:
        c.execute(
            "INSERT INTO notes(uid,lesson,body,ts) VALUES(?,?,?,?) "
            "ON CONFLICT(uid,lesson) DO UPDATE SET body=excluded.body, ts=excluded.ts",
            (n.uid, n.lesson, n.body, int(time.time())))
        c.commit()
    return {"ok": True}


@app.get("/api/stats")
def stats():
    with closing(db()) as c:
        learners = c.execute("SELECT COUNT(DISTINCT uid) FROM progress").fetchone()[0]
        done = c.execute("SELECT COUNT(*) FROM progress WHERE done=1").fetchone()[0]
    return {"learners": learners, "completions": done, "version": VERSION}


# ================================================================ 登录注册页（路由需在静态挂载前）
AUTH_PAGES = {
    "/login": "login.html",
    "/register": "register.html",
    "/pending": "pending.html",
    "/admin": "admin.html",
}


@app.get("/")
def index():
    return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/lesson/{lesson_id}/")
def lesson_page(lesson_id: str, request: Request):
    if not KEY_RE.match(lesson_id):
        raise HTTPException(404, "not found")
    p = WEB / "lesson" / lesson_id / "index.html"
    if not p.exists():
        raise HTTPException(404, "lesson not found")
    html = p.read_text(encoding="utf-8")

    # ---- 覆盖层与管理员编辑器：插在 app.js 之前，先应用覆盖，再让 app.js 绑定交互 ----
    user = current_user(request)
    is_admin = bool(user and user["role"] == "admin")
    inject = ""
    with closing(db()) as c:
        rows = c.execute(
            "SELECT chapter,title,body FROM section_overrides WHERE lesson=?", (lesson_id,)
        ).fetchall()
    ovs = {r["chapter"]: {"title": r["title"], "body": r["body"]}
           for r in rows if r["body"] or r["title"]}
    if ovs:
        inject += ("<script>window.ICL_OVERRIDES=" +
                   json.dumps(ovs, ensure_ascii=False) + ";</script>\n" + APPLY_JS + "\n")
    if is_admin:
        try:
            ver = int((WEB / "assets" / "editor.js").stat().st_mtime)
        except OSError:
            ver = 1
        inject += ('<script>window.ICL_ADMIN=true;</script>\n'
                   '<script src="/assets/editor.js?v=%d" defer></script>\n' % ver)
    if inject:
        marker = '<script src="/assets/app.js'
        if marker in html:
            html = html.replace(marker, inject + marker, 1)
        else:
            html = html.replace("</body>", inject + "</body>", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


# 覆盖层应用脚本（所有用户都会执行）：按 data-ch 找到小节，
# 换标题、把正文节点（跳过 :::{fig,svg} 展示块与"已学完"勾选框）替换成覆盖 HTML。
APPLY_JS = """<script>
(function(){
  var O=window.ICL_OVERRIDES||{};
  function bodyNodes(sec){
    return [].slice.call(sec.children).filter(function(n){
      if(n.classList.contains('ch-h'))return false;
      if(n.classList.contains('ch-done'))return false;
      if(n.matches('.fig-gallery,figure.fig-ai,figure.fig'))return false;
      return true;
    });
  }
  Object.keys(O).forEach(function(ch){
    var sec=document.querySelector('section.ch[data-ch="'+ch+'"]');
    if(!sec)return;
    var ov=O[ch];
    if(ov.title){var h=sec.querySelector('.ch-h h2');if(h)h.textContent=ov.title;}
    if(ov.body!=null){
      var label=sec.querySelector('label.ch-done');
      bodyNodes(sec).forEach(function(n){n.remove();});
      var tpl=document.createElement('template');tpl.innerHTML=ov.body;
      [].slice.call(tpl.content.childNodes).forEach(function(n){
        label?sec.insertBefore(n,label):sec.appendChild(n);
      });
      [].slice.call(sec.querySelectorAll('img')).forEach(function(im){
        if(!im.getAttribute('loading'))im.setAttribute('loading','lazy');
      });
    }
  });
})();
</script>"""


def _asset_ver() -> str:
    """assets 目录最新的 mtime 作为版本号，与 tools/build.py 的 bust() 同一口径：
    构建产物里写 logo.svg?v=xxx，登录/注册页由服务端注入同一个值，两边必须一致，
    否则改了 logo 之后首页刷新了、登录页还吃旧缓存。"""
    d = WEB / "assets"
    try:
        return str(int(max(p.stat().st_mtime for p in d.iterdir())))
    except (OSError, ValueError):
        return "1"


_ASSET_RE = re.compile(r"/assets/(logo\.svg|app\.css|app\.js|page\.js|shell\.js)(?:\?v=\d+)?")


def _auth_page(name: str):
    p = WEB / name
    if not p.exists():
        raise HTTPException(404, "page not found")
    html = p.read_text(encoding="utf-8")
    v = _asset_ver()
    html = _ASSET_RE.sub(lambda m: "/assets/%s?v=%s" % (m.group(1), v), html)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


for _path, _file in AUTH_PAGES.items():
    def _make(f):
        def _handler():
            return _auth_page(f)
        return _handler
    app.get(_path)(_make(_file))

# ================================================================ 图片服务（持久镜像优先）
# 管理员上传/替换的图存在 data/fig_mirror/（部署切换 web 不受影响），
# 这里必须注册在下面的 "/" 静态挂载之前，才能抢到 /fig/* 的请求。
FIG_SERVE_RE = re.compile(r"^[\w][\w\-./ ]*$")


@app.get("/fig/{fig_path:path}")
def fig_file(fig_path: str):
    if ".." in fig_path or not FIG_SERVE_RE.match(fig_path):
        raise HTTPException(404, "not found")
    p = MIRROR / fig_path
    if not p.exists():
        p = WEB / "fig" / fig_path
    if not p.exists():
        raise HTTPException(404, "fig not found")
    # 内容哈希命名的转存图内容不变 → 浏览器可长缓存；其余同名可替换 → 每次校验
    cc = ("public, max-age=31536000, immutable"
          if fig_path.startswith("custom/") else "no-cache")
    return FileResponse(p, headers={"Cache-Control": cc})


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")

# ================================================================ 全站访问控制
# /login /register /pending 公开；/admin 服务端强制管理员（见下方中间件）
PUBLIC_EXACT = {"/login", "/register", "/pending"} | {
    "/api/health", "/api/auth/register", "/api/auth/login", "/api/auth/logout",
    "/api/auth/me", "/favicon.ico", "/robots.txt",
}
PUBLIC_PREFIX = ("/assets/", "/api/auth/")


@app.middleware("http")
async def access_control(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIX):
        return await call_next(request)

    user = current_user(request)
    is_api = path.startswith("/api/")
    if user is None:
        if is_api:
            return JSONResponse({"detail": "not logged in"}, status_code=401)
        return RedirectResponse("/login?next=" + quote(path), status_code=302)

    approved = user["status"] == "approved" or user["role"] == "admin"
    if path == "/admin":
        if user["role"] != "admin":
            return RedirectResponse("/", status_code=302)
        return await call_next(request)

    if not approved:
        if is_api:
            return JSONResponse({"detail": "pending review"}, status_code=403)
        return RedirectResponse("/pending", status_code=302)
    return await call_next(request)


@app.middleware("http")
async def cache_control(request: Request, call_next):
    """HTML 一律 no-cache：页面里带着 /assets/xxx?v=版本号，只要 HTML 是新的，
    静态资源自然换新；反之 HTML 被浏览器启发式缓存，改了样式也看不到。
    静态资源反过来要长缓存——URL 里已有版本号，内容变了 URL 一定变。"""
    resp = await call_next(request)
    path = request.url.path
    if resp.status_code < 400:
        ctype = resp.headers.get("content-type", "")
        if path.startswith("/assets/"):
            resp.headers["Cache-Control"] = "public, max-age=604800"
        elif path.startswith("/fig/") and not path.startswith("/fig/custom/"):
            # 配图路径里没有版本号，同名换图必须立刻能看到；no-cache 只是"每次校验"，
            # 文件没变走 304，不重复传字节。fig/custom/ 是内容哈希命名，走长缓存。
            resp.headers["Cache-Control"] = "no-cache"
        elif ctype.startswith("text/html"):
            resp.headers["Cache-Control"] = "no-cache"
    return resp


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8710")))
