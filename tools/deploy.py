#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 + 打包 + 上传 + 原子切换 + 重启服务。

用法：
    python tools/deploy.py            # 构建并部署
    python tools/deploy.py --no-build # 只部署现有 web/
"""
import io
import os
import subprocess
import sys
import tarfile

from remote import put, sh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
REMOTE = "/home/weizhen/icacademy"
TARBALL = "/home/weizhen/icl_site.tar.gz"


def bundle():
    buf = io.BytesIO()
    n = 0
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for dirpath, _dirs, files in os.walk(WEB):
            for fn in files:
                if fn.endswith(".pyc") or fn.startswith("_"):
                    continue
                full = os.path.join(dirpath, fn)
                tar.add(full, arcname=os.path.relpath(full, WEB))
                n += 1
    return buf.getvalue(), n


def main():
    if "--no-build" not in sys.argv:
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "tools", "build.py")])
        if rc != 0:
            print("build failed")
            return rc

    data, n = bundle()
    print("bundle: %d files, %.1f KB" % (n, len(data) / 1024))
    put(data, TARBALL)

    # 解到新目录，验证无误后原子切换，避免上传失败导致站点空白
    cmd = (
        "set -e; cd {R}; "
        "rm -rf site_new; mkdir -p site_new data; "
        "tar xzf {T} -C site_new; "
        "test -f site_new/index.html; "
        "ts=$(date +%s); if [ -d web ]; then mv web web_old_$ts; fi; "
        "mv site_new web; "
        "sudo systemctl restart icacademy; sleep 2; "
        "sudo systemctl is-active icacademy; "
        "curl -s -m 5 http://127.0.0.1:8710/api/health; echo; "
        "curl -s -o /dev/null -w 'home:%{{http_code}} ' http://127.0.0.1:8710/; "
        "curl -s -o /dev/null -w 'lesson:%{{http_code}}\\n' http://127.0.0.1:8710/lesson/00-01-start/; "
        "du -sh web; ls web"
    ).format(R=REMOTE, T=TARBALL)
    rc, out, err = sh(cmd, timeout=300)
    if err.strip():
        print("[stderr]", err.strip()[:1200])
    return rc


if __name__ == "__main__":
    sys.exit(main())
