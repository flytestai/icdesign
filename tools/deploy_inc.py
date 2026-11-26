# -*- coding: utf-8 -*-
"""增量部署：本地算 md5 清单 -> 远端 md5sum -c 找差异 -> 只打包差异上传 -> 远端复核。

用法：
  python tools/deploy_inc.py            # 增量（默认）
  python tools/deploy_inc.py --full     # 强制全量（等同 deploy3）
  python tools/deploy_inc.py --no-restart  # 只传文件不重启服务
"""
import hashlib
import io
import os
import sys
import tarfile

import paramiko

HOST, USER = os.environ.get("ICL_HOST", "132.226.110.78"), os.environ.get("ICL_USER", "weizhen")
PWD = os.environ.get("ICL_PASS", "")
if not PWD:
    for line in open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".deploy.env"), encoding="utf-8"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ.setdefault(k, v)
    PWD = os.environ.get("ICL_PASS", "")
if not PWD:
    sys.exit("缺少密码：.deploy.env 或环境变量 ICL_PASS")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
REMOTE = "/home/weizhen/icacademy"
TAR = "/home/weizhen/icl_inc.tar.gz"


def connect():
    for i in range(3):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, 22, USER, PWD, timeout=30, banner_timeout=40, auth_timeout=40,
                      look_for_keys=False, allow_agent=False)
            c.get_transport().set_keepalive(10)
            return c
        except Exception as e:
            if i == 2:
                raise
            print(f"connect retry {i+1}: {e}")


def sh(c, cmd, timeout=300):
    _in, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="ignore")
    err = e.read().decode(errors="ignore")
    rc = o.channel.recv_exit_status()
    return rc, out, err


def local_manifest():
    """{relpath: md5}，排除 pyc / 下划线临时文件。"""
    out = {}
    for dirpath, _dirs, files in os.walk(WEB):
        for fn in files:
            if fn.endswith(".pyc") or fn.startswith("_"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, WEB).replace("\\", "/")
            out[rel] = hashlib.md5(open(full, "rb").read()).hexdigest()
    return out


def upload_bytes(c, remote, data):
    """单通道一次写入（exec_command + cat），写完校验 md5。"""
    sh(c, "rm -f " + remote)
    md5 = hashlib.md5(data).hexdigest()
    i, o, e = c.exec_command("cat > " + remote, timeout=120)
    i.write(data)
    i.flush()
    i.channel.shutdown_write()
    if o.channel.recv_exit_status() != 0:
        raise OSError("upload failed: " + remote)
    rc, out, _ = sh(c, "md5sum %s | cut -d' ' -f1" % remote)
    if out.strip() != md5:
        raise OSError("md5 mismatch: %s vs %s" % (out.strip(), md5))


def restart_service(c):
    i, o, e = c.exec_command(
        "sudo -S -p '' systemctl restart icacademy && sleep 3 && systemctl is-active icacademy && "
        "curl -s http://127.0.0.1:8710/api/health",
        timeout=120)
    i.write(PWD + "\n")
    i.flush()
    i.channel.shutdown_write()
    rc = o.channel.recv_exit_status()
    out = o.read().decode(errors="ignore").strip()
    err = e.read().decode(errors="ignore").strip()
    print("restart rc=%d %s %s" % (rc, out[:120], err[:200]))
    return rc == 0 and "active" in out


def main():
    full = "--full" in sys.argv
    no_restart = "--no-restart" in sys.argv
    c = connect()

    # 1) 远端对本地清单做 md5 校验，找出差异文件
    manifest = local_manifest()
    lines = "".join(f"{v}  {k}\n" for k, v in manifest.items()).encode()
    upload_bytes(c, "/home/weizhen/.icl_manifest.txt", lines)
    rc, out, _ = sh(c, f"cd {REMOTE}/web && md5sum -c /home/weizhen/.icl_manifest.txt 2>/dev/null | grep -v ': OK$' || true", timeout=120)
    changed = [l.rsplit(": ", 1)[0] for l in out.splitlines() if ": " in l and not l.endswith(": OK")]
    if full:
        changed = list(manifest.keys())
    # 远端多出来的文件（本地已删）不在此清单里，增量不管；需要清理时用 --full 或手动
    print(f"本地文件 {len(manifest)} 个，差异 {len(changed)} 个")

    # 2) 只打包差异
    buf = io.BytesIO()
    n = 0
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel in changed:
            full_path = os.path.join(WEB, rel.replace("/", os.sep))
            tar.add(full_path, arcname=rel)
            n += 1
    data = buf.getvalue()
    print(f"打包 {n} 个文件，{len(data)/1048576:.2f} MB")

    # 3) 单通道上传
    upload_bytes(c, TAR, data)

    # 4) 解包 + 复核 + 清理
    rc, out, err = sh(c, f"cd {REMOTE}/web && tar xzf {TAR} && md5sum -c /home/weizhen/.icl_manifest.txt 2>/dev/null | grep -v ': OK$' || true", timeout=120)
    bad = [l for l in out.splitlines() if l.strip() and not l.endswith(": OK")]
    sh(c, f"rm -f {TAR} /home/weizhen/.icl_manifest.txt")
    if bad:
        print("复核不一致：", bad[:10])
        sys.exit(1)
    print("远端复核 0 不一致")

    # 5) 上传 server/app.py + 重启
    app_src = os.path.join(ROOT, "server", "app.py")
    app_data = open(app_src, "rb").read()
    rc, out, _ = sh(c, f"md5sum {REMOTE}/app.py 2>/dev/null | cut -d' ' -f1")
    if out.strip() != hashlib.md5(app_data).hexdigest():
        upload_bytes(c, REMOTE + "/app.py", app_data)
        print("app.py 已更新")
    else:
        print("app.py 无变化")
    if not no_restart:
        restart_service(c)
    c.close()
    print("完成")


if __name__ == "__main__":
    main()
