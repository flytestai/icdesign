#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量 UI 部署：只上传本轮变更的 server/app.py + web 下改动文件（git diff 列表），不重传全站。

    python tools/deploy_ui.py            # 自动取 git 变更列表
    python tools/deploy_ui.py <file>...  # 显式指定相对路径
"""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramiko  # noqa: E402
from remote import HOST, USER, PWD  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "/home/weizhen/icacademy"


def sh(c, cmd, timeout=300):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="ignore")
    err = e.read().decode(errors="ignore")
    return o.channel.recv_exit_status(), out, err


def put(c, data, remote):
    i, o, e = c.exec_command("cat > " + remote, timeout=120)
    i.write(data)
    i.flush()
    i.channel.shutdown_write()
    return o.channel.recv_exit_status() == 0


def restart(c):
    i, o, e = c.exec_command(
        "sudo -S -p '' systemctl restart icacademy && sleep 3 && systemctl is-active icacademy",
        timeout=120)
    i.write(PWD + "\n")
    i.flush()
    i.channel.shutdown_write()
    out = o.read().decode(errors="ignore").strip()
    return "active" in out, out[:120]


def changed_files():
    out = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT, capture_output=True, text=True).stdout
    files = []
    for f in out.splitlines():
        f = f.strip()
        if f.startswith("server/") or f.startswith("web/"):
            if f.endswith(".pyc") or os.path.basename(f).startswith("_"):
                continue
            files.append(f)
    return files


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = changed_files()
    if not files:
        print("没有变更文件")
        return 0
    print("待上传 %d 个文件：" % len(files))
    payloads = []
    for f in files:
        p = os.path.join(ROOT, f.replace("/", os.sep))
        if not os.path.isfile(p):
            print("  !! 缺少本地文件，跳过:", f)
            continue
        payloads.append((f, open(p, "rb").read()))

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PWD, timeout=30, banner_timeout=60, auth_timeout=60,
              look_for_keys=False, allow_agent=False)
    try:
        need_restart = False
        for rel, data in payloads:
            # server/app.py 在远端位于根目录（无 server/ 子目录）
            remote = BASE + "/app.py" if rel == "server/app.py" else BASE + "/" + rel
            ok = put(c, data, remote + ".new")
            rc, out, _ = sh(c, "md5sum %s.new | cut -d' ' -f1" % remote)
            good = ok and out.strip() == hashlib.md5(data).hexdigest()
            if not good:
                print("  !! 校验不一致:", rel, out.strip()[:12], "vs", hashlib.md5(data).hexdigest()[:12])
                return 1
            sh(c, "mv %s.new %s" % (remote, remote))
            print("  ok %-44s %.1f KB" % (rel, len(data) / 1024))
            if rel.startswith("server/") or rel.endswith(".js"):
                need_restart = True

        if need_restart:
            active, out = restart(c)
            print("restart:", out)
            if not active:
                return 1
            rc, out, _ = sh(c, "curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8710/api/health")
            print("health:", out)
            return 0 if out == "200" else 1
        print("无需重启（仅 HTML/数据变更）")
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
