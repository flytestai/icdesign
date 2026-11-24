# -*- coding: utf-8 -*-
"""部署（分块上传版）：单连接、8KB 分块追加，避开大块写入被重置的问题。"""
import hashlib
import io
import os
import subprocess
import sys
import tarfile
import time

import paramiko

HOST, USER = os.environ.get("ICL_HOST", "132.226.110.78"), os.environ.get("ICL_USER", "weizhen")
PWD = os.environ.get("ICL_PASS", "")
if not PWD:
    sys.exit("缺少密码：请先设置环境变量 ICL_PASS（不要把密码写进代码或提交到仓库）")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
REMOTE = "/home/weizhen/icacademy"
TAR = "/home/weizhen/icl_site.tar.gz"
CHUNK = 8192


def connect(retries=3):
    """连不上就重试：偶尔会出现连接刚建好就被服务器重置（WinError 10054）。"""
    last = None
    for k in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, 22, USER, PWD, timeout=30, banner_timeout=40, auth_timeout=40,
                      look_for_keys=False, allow_agent=False)
            c.get_transport().set_keepalive(15)
            return c
        except Exception as e:
            last = e
            print("连接失败（%d/%d）：%s" % (k + 1, retries, str(e)[:120]))
            time.sleep(3 * (k + 1))
    raise SystemExit("连不上服务器：%s" % last)


def sh(c, cmd, timeout=300):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="ignore")
    err = e.read().decode(errors="ignore")
    rc = o.channel.recv_exit_status()
    return rc, out, err


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


def upload_app(c):
    """上传 server/app.py 到远端根目录（分块追加，与站点同一通道）。"""
    src = os.path.join(ROOT, "server", "app.py")
    data = open(src, "rb").read()
    md5 = hashlib.md5(data).hexdigest()
    remote = "/home/weizhen/icacademy/app.py"
    sh(c, "rm -f /home/weizhen/icl_app.py.new")
    for k in range((len(data) + CHUNK - 1) // CHUNK):
        part = data[k * CHUNK:(k + 1) * CHUNK]
        i, o, e = c.exec_command("cat >> /home/weizhen/icl_app.py.new", timeout=60)
        i.write(part)
        i.flush()
        i.channel.shutdown_write()
        if o.channel.recv_exit_status() != 0:
            print("app.py chunk %d failed" % k)
            return False
    rc, out, _ = sh(c, "md5sum /home/weizhen/icl_app.py.new | cut -d' ' -f1")
    if out.strip() != md5:
        print("!! app.py 校验不一致: %s vs %s" % (out.strip(), md5))
        return False
    sh(c, "mv /home/weizhen/icl_app.py.new " + remote)
    print("app.py uploaded, md5=%s" % md5)
    return True


def restart_service(c):
    """用 sudo -S 重启服务（密码从 stdin 传入，不写进命令行）。"""
    i, o, e = c.exec_command(
        "sudo -S -p '' systemctl restart icacademy && sleep 3 && systemctl is-active icacademy",
        timeout=120)
    i.write(PWD + "\n")
    i.flush()
    i.channel.shutdown_write()
    rc = o.channel.recv_exit_status()
    out = o.read().decode(errors="ignore").strip()
    err = e.read().decode(errors="ignore").strip()
    print("restart rc=%d %s %s" % (rc, out[:120], err[:200]))
    return rc == 0 and "active" in out


def upload_package(c, data, remote):
    """整包一次写入（一条通道）。

    老办法是 8KB 一片、每片开一个 exec_command 通道：站点小的时候没事，
    图库涨到 40MB 后要开 5000 多个通道，传到 1MB 服务器就把连接重置了。
    实测单通道一次写 43MB / 150 秒完全稳定，就照这个来。"""
    i, o, e = c.exec_command("cat > " + remote, timeout=900)
    i.write(data)
    i.flush()
    i.channel.shutdown_write()
    return o.channel.recv_exit_status() == 0


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
        sh(c, "rm -f " + TAR)
        print("uploading %.1f MB …" % (len(data) / 1048576.0))
        upload_package(c, data, TAR)

        rc, out, _ = sh(c, "stat -c %s " + TAR + "; md5sum " + TAR + " | cut -d' ' -f1")
        lines = [x for x in out.strip().split("\n") if x]
        print("remote size=%s md5=%s" % (lines[0] if lines else "?", lines[-1] if lines else "?"))
        if len(lines) < 2 or lines[-1] != md5:
            print("!! 校验不一致，停止部署")
            return 1

        rc, out, err = sh(c, (
            "set -e; cd %s; rm -rf site_new; mkdir -p site_new; "
            "tar xzf %s -C site_new; "
            "test -f site_new/index.html; test -f site_new/quiz/index.html; "
            "echo extracted=$(find site_new -type f | wc -l)" % (REMOTE, TAR)))
        print(out.strip(), err.strip()[:300])

        rc, out, err = sh(c, (
            "set -e; cd %s; ts=$(date +%%s); "
            "if [ -d web ]; then mv web web_old_$ts; fi; mv site_new web; "
            "ls -d web" % REMOTE), timeout=180)
        print(out.strip(), err.strip()[:300])

        if not upload_app(c):
            return 1
        restart_service(c)

        time.sleep(2)
        rc, out, err = sh(c, (
            "for p in / /login /register /admin /playground/ /quiz/ /glossary/ /abbr/ /search/ /progress/ /cheatsheet/ "
            "/lesson/01-01-linux-01-intro/ /lesson/01-06-linux-06-sed-awk/ "
            "/lesson/01-07-tcl-01-start/ /lesson/01-11-tcl-05-list-a/ /lesson/01-13-tcl-07-if/ "
            "/lesson/01-14-tcl-08-loops/ /lesson/01-16-tcl-10-final/ /data/quiz.json "
            "/data/catalog.json /assets/tcl.js /assets/shell.js /fig/linux-01.png /fig/tcl-02.png; do "
            "printf '%s -> ' $p; curl -s -o /dev/null -w '%{http_code}\\n' -m 8 http://127.0.0.1:8710$p; done; "
            "echo '--- 带管理员会话 ---'; "
            "TOKEN=$(curl -s -i -X POST http://127.0.0.1:8710/api/auth/login -H 'Content-Type: application/json' "
            "-d '{\"account\":\"weizhen\",\"password\":\"wz729729\"}' | grep -oP 'ic_session=\\K[a-f0-9]{64}'); "
            "for p in / /lesson/01-02-tcl-01-start/ /api/admin/users; do "
            "printf '%s -> ' $p; curl -s -o /dev/null -w '%{http_code}\\n' -m 8 -H \"Cookie: ic_session=$TOKEN\" http://127.0.0.1:8710$p; done"), timeout=180)
        print(out.strip())
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    sys.exit(main())
