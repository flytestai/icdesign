"""极简 SSH 执行/上传（paramiko）。凭据从 .deploy.env 或环境变量读。"""
import os
import paramiko

_here = os.path.dirname(os.path.abspath(__file__))


def _load_env():
    p = os.path.join(_here, "..", ".deploy.env")
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
    _in, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode("utf-8", "replace")
    e = err.read().decode("utf-8", "replace")
    rc = out.channel.recv_exit_status()
    c.close()
    if not quiet:
        if o.strip():
            print(o.rstrip())
        if e.strip():
            print("[stderr]", e.rstrip()[:2000])
    return rc, o, e


def put(data, remote):
    if isinstance(data, str) and os.path.exists(data):
        data = open(data, "rb").read()
    elif isinstance(data, str):
        data = data.encode()
    c = client()
    d = os.path.dirname(remote)
    if d:
        c.exec_command("mkdir -p %s" % d)[1].read()
    _in, out, err = c.exec_command("cat > %s" % remote, timeout=300)
    _in.write(data)
    _in.flush()
    _in.channel.shutdown_write()
    rc = out.channel.recv_exit_status()
    e = err.read().decode("utf-8", "replace")
    c.close()
    if rc != 0:
        raise RuntimeError("put failed: %s" % e)
    return len(data)
