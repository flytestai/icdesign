"""极简远程执行/传输：ext 通道 + cat 重定向，绕开 SFTP 限制。"""
import sys, os, paramiko
def _load_env():
    """凭据写在项目根目录 .deploy.env（不入库），或用环境变量覆盖。"""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".deploy.env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
HOST = os.environ.get("ICL_HOST", "132.226.110.78")
USER = os.environ.get("ICL_USER", "weizhen")
PWD = os.environ.get("ICL_PASS", "")

def client():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PWD, timeout=25, banner_timeout=40,
              auth_timeout=40, allow_agent=False, look_for_keys=False)
    return c

def sh(cmd, timeout=600, quiet=False):
    c = client()
    si, so, se = c.exec_command(cmd, timeout=timeout, get_pty=False)
    out = so.read().decode("utf-8", "replace")
    err = se.read().decode("utf-8", "replace")
    rc = so.channel.recv_exit_status()
    c.close()
    if not quiet:
        if out.strip(): print(out.rstrip())
        if err.strip(): print("[stderr]", err.rstrip()[:3000])
    return rc, out, err

def put(local, remote):
    data = open(local, "rb").read() if isinstance(local, str) else local
    c = client()
    d = os.path.dirname(remote)
    if d:
        c.exec_command("mkdir -p %s" % d)[1].read()
    si, so, se = c.exec_command("cat > %s" % remote, timeout=300)
    si.write(data); si.flush(); si.channel.shutdown_write()
    rc = so.channel.recv_exit_status()
    err = se.read().decode("utf-8", "replace")
    c.close()
    if rc != 0:
        raise RuntimeError("put failed %s: %s" % (remote, err))
    return len(data)

if __name__ == "__main__":
    if sys.argv[1] == "sh":
        sh(sys.argv[2])
    elif sys.argv[1] == "put":
        n = put(sys.argv[2], sys.argv[3]); print("put", sys.argv[3], n, "bytes")
