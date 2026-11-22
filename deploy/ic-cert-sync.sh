#!/bin/bash
# 把 acme.sh 续期后的证书同步到 nginx 目录并重载
set -e
SRC=/home/ubuntu/.acme.sh/ic.feice.net_ecc
DST=/etc/nginx/ssl/ic.feice.net
cp "$SRC/fullchain.cer" "$DST/fullchain.pem"
cp "$SRC/ic.feice.net.key" "$DST/privkey.pem"
chmod 600 "$DST/privkey.pem"
nginx -t >/dev/null 2>&1 && systemctl reload nginx
echo "$(date '+%F %T') synced"
