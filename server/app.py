#!/usr/bin/env python3
"""
IC 后端学院 · 后端服务
- 静态站点托管（web/）
- 课程目录 API
- 学习进度同步（匿名设备 ID）
- 课后笔记
"""
import json
import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(os.environ.get("ICL_BASE", Path(__file__).resolve().parent))
WEB = BASE / "web"
DATA = BASE / "data"
DB = DATA / "app.db"
VERSION = "1.0.0"

DATA.mkdir(exist_ok=True)

app = FastAPI(title="IC 后端学院 API", version=VERSION, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=1024)

UID_RE = re.compile(r"^[A-Za-z0-9_\-]{4,40}$")
KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{1,48}$")


def db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with closing(db()) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS progress(
            uid TEXT NOT NULL, lesson TEXT NOT NULL, chapter TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 1, ts INTEGER NOT NULL,
            PRIMARY KEY(uid, lesson, chapter))""")
        c.execute("""CREATE TABLE IF NOT EXISTS notes(
            uid TEXT NOT NULL, lesson TEXT NOT NULL, body TEXT NOT NULL, ts INTEGER NOT NULL,
            PRIMARY KEY(uid, lesson))""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_progress_uid ON progress(uid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_progress_lesson ON progress(lesson)")
        c.commit()


init_db()


def check_uid(uid: str):
    if not UID_RE.match(uid or ""):
        raise HTTPException(status_code=400, detail="invalid uid")


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


# ---------------- 静态站点 ----------------
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


app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8710")))
