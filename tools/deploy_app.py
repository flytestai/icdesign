#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量部署：只传 server/app.py + web/assets/editor.js 并重启服务（不重传全站）。

    python tools/deploy_app.py
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramiko  # noqa: E402
from remote import HOST, USER, PWD  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_REMOTE = "/home/weizhen/icacademy/app.py"
ED_REMOTE = "/home/weizhen/icacademy/web/assets/editor.js"


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


def main():
    app = open(os.path.join(ROOT, "server", "app.py"), "rb").read()
    ed = open(os.path.join(ROOT, "web", "assets", "editor.js"), "rb").read()
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PWD, timeout=30, banner_timeout=60, auth_timeout=60,
              look_for_keys=False, allow_agent=False)
    try:
        ok = put(c, app, APP_REMOTE + ".new")
        rc, out, _ = sh(c, "md5sum %s.new | cut -d' ' -f1" % APP_REMOTE)
        assert ok and out.strip() == hashlib.md5(app).hexdigest(), "app.py 校验不一致"
        sh(c, "mv %s.new %s" % (APP_REMOTE, APP_REMOTE))
        print("app.py ok (%.1f KB)" % (len(app) / 1024))

        ok = put(c, ed, ED_REMOTE + ".new")
        rc, out, _ = sh(c, "md5sum %s.new | cut -d' ' -f1" % ED_REMOTE)
        assert ok and out.strip() == hashlib.md5(ed).hexdigest(), "editor.js 校验不一致"
        sh(c, "mv %s.new %s" % (ED_REMOTE, ED_REMOTE))
        print("editor.js ok (%.1f KB)" % (len(ed) / 1024))

        active, out = restart(c)
        print("restart:", out)
        if not active:
            return 1
        rc, out, _ = sh(c, "curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8710/api/health")
        print("health:", out)
        return 0 if out == "200" else 1
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
