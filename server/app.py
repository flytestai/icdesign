#!/usr/bin/env python3
"""
IC 后端学院 · 后端服务
- 静态站点托管（web/）
- 课程目录 API
- 学习进度同步（匿名设备 ID）
- 课后笔记
- 用户注册 / 登录 / 管理员审核（未通过审核不能看课程内容）
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(os.environ.get("ICL_BASE", Path(__file__).resolve().parent))
WEB = BASE / "web"
DATA = BASE / "data"
DB = DATA / "app.db"
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
                ("管理员", ADMIN_ACCOUNT, "", hash_password(ADMIN_PASSWORD, salt), salt,
                 "admin", "approved", now, now))
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
        u = c.execute("SELECT * FROM users WHERE account=?", (account,)).fetchone()
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
def lesson_page(lesson_id: str):
    if not KEY_RE.match(lesson_id):
        raise HTTPException(404, "not found")
    p = WEB / "lesson" / lesson_id / "index.html"
    if not p.exists():
        raise HTTPException(404, "lesson not found")
    return FileResponse(p, headers={"Cache-Control": "no-cache"})


def _auth_page(name: str):
    p = WEB / name
    if not p.exists():
        raise HTTPException(404, "page not found")
    return FileResponse(p, headers={"Cache-Control": "no-cache"})


for _path, _file in AUTH_PAGES.items():
    def _make(f):
        def _handler():
            return _auth_page(f)
        return _handler
    app.get(_path)(_make(_file))

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8710")))
