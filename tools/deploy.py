#!/usr/bin/env python3
"""打包并部署到服务器（应用文件 + systemd 重启）"""
import io, os, sys, tarfile, time
from remote import sh, put

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
APP = os.path.join(ROOT, "server", "app.py")
REMOTE_DIR = "/home/weizhen/icacademy"

SKIP = {"home.html"}


def bundle():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for dirpath, dirnames, filenames in os.walk(WEB):
            for fn in filenames:
                if fn.startswith("_") or fn in SKIP:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, os.path.join(ROOT))
                tar.add(full, arcname=rel)
        tar.add(APP, arcname="app.py")
    return buf.getvalue()


def main():
    data = bundle()
    print("bundle: %.1f KB" % (len(data) / 1024))
    put(data, "/home/weizhen/icl_deploy.tar.gz")

    rc, out, err = sh("set -e; cd %s && mkdir -p web data && "
                      "tar xzf /home/weizhen/icl_deploy.tar.gz -C %s && "
                      "ls -la %s && du -sh %s/web" % (REMOTE_DIR, REMOTE_DIR, REMOTE_DIR, REMOTE_DIR))
    if rc != 0:
        print(out, err)
        sys.exit(rc)

    rc, out, err = sh("sudo systemctl restart icacademy && sleep 2 && "
                      "sudo systemctl is-active icacademy && "
                      "curl -s -m 5 http://127.0.0.1:8710/api/health; echo; "
                      "curl -s -o /dev/null -w 'index:%{http_code} ' http://127.0.0.1:8710/; "
                      "curl -s -o /dev/null -w 'lesson:%{http_code}\\n' http://127.0.0.1:8710/lesson/01-flow/")
    print(out.strip())
    if err.strip():
        print("[stderr]", err.strip()[:1500])


if __name__ == "__main__":
    main()
