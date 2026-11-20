#!/usr/bin/env bash
# Points the LIVE ovd-backend unit at /opt/ovd-next with the real env file. Auto-rolls back on a failed health check.
set -euo pipefail
NEW=/opt/ovd-next; ENVF=/etc/ovd-next.env; U=/etc/systemd/system/ovd-backend.service
grep -q '^DODO_PAYMENTS_WEBHOOK_SECRET=whsec_' "$ENVF" || { echo "webhook secret missing"; exit 1; }
BK=/root/backups/ovd-backend.service.pre-cutover.$(date +%Y%m%d-%H%M%S); cp "$U" "$BK"
sed -i -e "s#/opt/ovd-backend#$NEW#g" -e "/^User=root/a EnvironmentFile=$ENVF\nEnvironment=\"JOBS_DIR=/var/lib/ovd-jobs\"" "$U"
mkdir -p /var/lib/ovd-jobs
systemctl daemon-reload && systemctl restart ovd-backend
for i in $(seq 1 20); do
  sleep 2
  if curl -sf -m 5 http://127.0.0.1:8000/api/auth/config >/dev/null; then echo "HEALTHY after $((i*2))s"; systemctl is-active ovd-backend; exit 0; fi
done
echo "UNHEALTHY -> rolling back"; cp "$BK" "$U"; systemctl daemon-reload; systemctl restart ovd-backend; sleep 4
systemctl is-active ovd-backend; journalctl -u ovd-backend -n 25 --no-pager; exit 1
