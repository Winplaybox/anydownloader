#!/usr/bin/env bash
# Safe, idempotent: backs up the live OVD service and starts the NEW code on 127.0.0.1:8001
# with TEST data dirs. Never touches the live ovd-backend service.
set -euo pipefail
OLD=/opt/ovd-backend; NEW=/opt/ovd-next; ENVF=/etc/ovd-next.env
TS=$(date +%Y%m%d-%H%M%S); BK=/root/backups; mkdir -p "$BK" /var/lib/ovd-next/{data,jobs,autoclip}
tar czf "$BK/ovd-backend-$TS.tgz" -C /opt ovd-backend
cp /etc/systemd/system/ovd-backend.service "$BK/ovd-backend.service.$TS"
for f in $(find /var/tmp /var/lib /opt/ovd-backend -maxdepth 3 -name 'auth.db' 2>/dev/null | grep -v ovd-next); do
  python3 - "$f" "$BK/$(echo "$f" | tr / _).$TS" <<'PY'
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
PY
  echo "backed up $f"
done
gen() { openssl rand -hex 32; }
if [ ! -f "$ENVF" ]; then
  umask 077
  cat > "$ENVF" <<ENV
WPB_JWT_SECRET=$(gen)
EXTENSION_SECRET_KEY=$(gen)
TOKEN_HMAC_SECRET=$(gen)
JOB_OWNER_SECRET=$(gen)
GOOGLE_CLIENT_ID=259545227984-tq7m462dc4vkqfv1g1ch66mou7uhigki.apps.googleusercontent.com
WPB_ADMIN_EMAILS=sagarsuthar530@gmail.com
DODO_PAYMENTS_WEBHOOK_SECRET=whsec_$(openssl rand -base64 24)
ENV
  echo "created $ENVF"
fi
# test-only overrides live in the unit, NOT in $ENVF, so cutover can reuse $ENVF unchanged
sed -e "s#/opt/ovd-backend#$NEW#g" -e 's#PORT=8000#PORT=8001#' -e 's#--port 8000#--port 8001#' \
    -e "s#AUTOCLIP_DATA_DIR=.*#AUTOCLIP_DATA_DIR=/var/lib/ovd-next/autoclip\"#" \
    -e "/^User=root/a EnvironmentFile=$ENVF\nEnvironment=\"WPB_DATA_DIR=/var/lib/ovd-next/data\"\nEnvironment=\"JOBS_DIR=/var/lib/ovd-next/jobs\"" \
    "$BK/ovd-backend.service.$TS" > /etc/systemd/system/ovd-next.service
systemctl daemon-reload && systemctl restart ovd-next
sleep 8
systemctl is-active ovd-next
curl -s -m 8 -o /dev/null -w "root: %{http_code}\n" http://127.0.0.1:8001/
curl -s -m 8 http://127.0.0.1:8001/api/auth/config | head -c 300; echo
journalctl -u ovd-next -n 15 --no-pager | tail -15
