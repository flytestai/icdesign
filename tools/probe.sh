echo "--python--"; python3 -V
echo "--node--"; (node -v 2>/dev/null || echo no-node)
echo "--nginx--"; (nginx -v 2>&1 || echo no-nginx)
echo "--ports--"; (ss -lntp 2>/dev/null | grep -E ':(80|443|8000|3000|8080)' || echo none)
echo "--sudo--"; (sudo -n true 2>&1 && echo SUDO_OK || echo SUDO_NEED_PWD)
echo "--firewall--"; systemctl is-active firewalld 2>/dev/null || echo firewalld-inactive
echo "--net--"; (curl -s -m 8 -o /dev/null -w '%{http_code}' https://pypi.org/simple/ ; echo)
echo "--dns--"; getent hosts ic.feice.net
echo "--home--"; ls -la ~ | head -20
