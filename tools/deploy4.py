# -*- coding: utf-8 -*-
"""部署 v4：SFTP 直传（比 shell 里 cat >> 稳），失败自动重试与回退分块上传。

用法：
    ICL_PASS=*** python tools/deploy4.py            # 构建 + 部署
    ICL_PASS=*** python tools/deploy4.py --no-build # 只部署现有 web/

流程：打包 → 上传（SFTP，失败退回分块）→ 远端 md5 校验 → 解到 site_new → 原子切换 → 逐路由探活
"""
import hashlib
import io
import os
import subprocess
import sys
import tarfile
import time

import paramiko

HOST = os.environ.get("ICL_HOST", "132.226.110.78")
USER = os.environ.get("ICL_USER", "weizhen")
PWD = os.environ.get("ICL_PASS", "")
if not PWD:
    sys.exit("缺少密码：请先设置环境变量 ICL_PASS（不要把密码写进代码或提交到仓库）")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
REMOTE = "/home/weizhen/icacademy"
TAR = "/home/weizhen/icl_site.tar.gz"
CHUNK = 8192
ROUTES = ["/", "/quiz/", "/glossary/", "/abbr/", "/search/", "/progress/", "/cheatsheet/",
          "/lesson/03-08-cts/", "/lesson/05-02-pt/", "/data/quiz.json", "/assets/shell.js"]


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PWD, timeout=30, banner_timeout=60, auth_timeout=60,
              look_for_keys=False, allow_agent=False)
    t = c.get_transport()
    t.set_keepalive(15)
    t.window_size = 4 * 1024 * 1024
    t.packetizer.REKEY_BYTES = 1 << 30
    return c


def sh(c, cmd, timeout=300):
    _i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="ignore")
    err = e.read().decode(errors="ignore")
    return o.channel.recv_exit_status(), out, err


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


def upload_sftp(c, data):
    sftp = c.open_sftp()
    try:
        with sftp.file(TAR, "wb") as f:
            f.set_pipelined(True)
            view = memoryview(data)
            step = 64 * 1024
            for i in range(0, len(data), step):
                f.write(view[i:i + step])
    finally:
        sftp.close()


def upload_chunks(c, data):
    sh(c, "rm -f " + TAR)
    chunks = (len(data) + CHUNK - 1) // CHUNK
    for k in range(chunks):
        part = data[k * CHUNK:(k + 1) * CHUNK]
        for attempt in range(3):
            try:
                i, o, _e = c.exec_command("cat >> " + TAR, timeout=90)
                i.write(part)
                i.flush()
                i.channel.shutdown_write()
                rc = o.channel.recv_exit_status()
                if rc != 0:
                    raise IOError("rc=%d" % rc)
                break
            except Exception as ex:  # 单块失败重连重试
                print("  chunk %d retry %d: %s" % (k, attempt + 1, ex))
                time.sleep(2 + attempt * 3)
                if attempt == 2:
                    return False
    print("uploaded %d chunks" % chunks)
    return True


def remote_md5(c):
    _rc, out, _err = sh(c, "md5sum " + TAR + " | cut -d' ' -f1; stat -c %s " + TAR)
    lines = [x.strip() for x in out.strip().split("\n") if x.strip()]
    return (lines[0], lines[1]) if len(lines) >= 2 else ("?", "?")


def main():
    if "--no-build" not in sys.argv:
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "tools", "build.py")])
        if rc != 0:
            print("build failed")
            return rc

    data, n = bundle()
    md5 = hashlib.md5(data).hexdigest()
    print("bundle: %d files, %.0f KB, md5=%s" % (n, len(data) / 1024, md5))

    c = connect()
    try:
        ok = False
        for mode in ("sftp", "chunk"):
            try:
                if mode == "sftp":
                    upload_sftp(c, data)
                    rmd5, rsize = remote_md5(c)
                    ok = rmd5 == md5
                    print("sftp: size=%s md5=%s %s" % (rsize, rmd5, "OK" if ok else "MISMATCH"))
                else:
                    if not upload_chunks(c, data):
                        continue
                    rmd5, rsize = remote_md5(c)
                    ok = rmd5 == md5
                    print("chunk: size=%s md5=%s %s" % (rsize, rmd5, "OK" if ok else "MISMATCH"))
            except Exception as ex:
                print("%s 上传失败：%s" % (mode, ex))
                try:
                    c.close()
                except Exception:
                    pass
                time.sleep(3)
                c = connect()
                continue
            if ok:
                break

        if not ok:
            print("!! 校验不一致，停止部署（线上旧版本保持不动）")
            return 1

        _rc, out, err = sh(c, (
            "set -e; cd %s; rm -rf site_new; mkdir -p site_new; "
            "tar xzf %s -C site_new; test -f site_new/index.html; test -f site_new/quiz/index.html; "
            "echo extracted=$(find site_new -type f | wc -l)" % (REMOTE, TAR)))
        print(out.strip(), err.strip()[:300])
        if "extracted=" not in out:
            print("!! 解包失败，线上旧版本保持不动")
            return 1

        _rc, out, err = sh(c, (
            "set -e; cd %s; ts=$(date +%%s); "
            "if [ -d web ]; then mv web web_old_$ts; fi; mv site_new web; ls -d web; "
            "(systemctl restart icacademy || sudo -n systemctl restart icacademy) 2>&1 | tail -2; "
            "sleep 3; systemctl is-active icacademy" % REMOTE), timeout=180)
        print(out.strip(), err.strip()[:200])

        time.sleep(2)
        _rc, out, _err = sh(c, (
            "for p in %s; do printf '%%s -> ' $p; "
            "curl -s -o /dev/null -w '%%{http_code}\\n' -m 10 http://127.0.0.1:8710$p; done" % " ".join(ROUTES)),
            timeout=180)
        print(out.strip())
        bad = [l for l in out.split("\n") if l.strip() and not l.strip().endswith("200")]
        if bad:
            print("!! 以下路由异常：")
            print("\n".join(bad))
            return 1
        print("deploy ok: %d 路由全部 200" % len(ROUTES))
        return 0
    finally:
        try:
            c.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
