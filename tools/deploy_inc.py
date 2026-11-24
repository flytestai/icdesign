#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增量部署：只传变化的文件。

全量打包现在要 40MB+（图库还会涨），每次改几节课都传一遍太慢。
做法：本地算一份 md5 清单 → 丢给服务器 `md5sum -c` → 它把不认识/对不上的路径吐回来
→ 只把这些文件打包传过去解包。

    python tools/deploy_inc.py            # 增量同步
    python tools/deploy_inc.py --full     # 强制全量（换机器或怀疑不一致时）

凭据与 deploy3 一致：ICL_PASS 或 .deploy.env。
"""
import hashlib
import io
import os
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import remote  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
REMOTE_WEB = "/home/weizhen/icacademy/web"
MANIFEST = "/tmp/ic_manifest.lst"
PKG = "/home/weizhen/ic_inc.tgz"


def local_manifest():
    rows = []
    for dp, _dirs, files in os.walk(WEB):
        for fn in files:
            if fn.endswith(".pyc") or fn.startswith("_"):
                continue
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, WEB).replace("\\", "/")
            rows.append((rel, hashlib.md5(open(full, "rb").read()).hexdigest()))
    rows.sort()
    return rows


def main():
    t0 = time.time()
    rows = local_manifest()
    print("本地文件 %d 个" % len(rows))
    if "--full" in sys.argv:
        need = [r for r, _ in rows]
    else:
        remote.put("\n".join("%s  %s" % (m, r) for r, m in rows) + "\n", MANIFEST)
        # md5sum -c 只输出对不上的行（包含缺失文件）
        rc, out, _ = remote.sh("cd %s && md5sum -c %s 2>/dev/null | grep -v ': OK$' | cut -d: -f1"
                               % (REMOTE_WEB, MANIFEST), quiet=True)
        need = [x.strip() for x in out.splitlines() if x.strip()]
        need = [x for x in need if os.path.exists(os.path.join(WEB, x))]
        print("需要更新 %d 个文件" % len(need))
    if not need:
        print("已是最新，耗时 %.0fs" % (time.time() - t0))
        return 0

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=1) as tar:
        for rel in need:
            tar.add(os.path.join(WEB, rel), arcname=rel)
    data = buf.getvalue()
    print("打包 %.1f MB" % (len(data) / 1048576.0))
    remote.put(data, PKG)

    rc, out, err = remote.sh("set -e; tar xzf %s -C %s; echo unpacked; rm -f %s" % (PKG, REMOTE_WEB, PKG),
                             quiet=True, timeout=300)
    print("解包 rc=%s %s %s" % (rc, out.strip()[:120], err.strip()[:200]))

    # 复核：把清单再过一遍，确认没有漏网
    rc, out, _ = remote.sh("cd %s && md5sum -c %s 2>/dev/null | grep -vc ': OK$'" % (REMOTE_WEB, MANIFEST),
                           quiet=True)
    bad = out.strip().splitlines()[-1] if out.strip() else "?"
    print("复核：不一致 %s 个；耗时 %.0fs" % (bad, time.time() - t0))
    return 0 if bad in ("0", "") else 1


if __name__ == "__main__":
    sys.exit(main())
