#!/usr/bin/env sh
# Nightly consistent backup of OVD's SQLite databases (users, credits, payments, jobs).
# Cron on the VPS host:  17 3 * * * /opt/ovd/deploy/backup.sh >> /var/log/ovd-backup.log 2>&1
set -eu
cd "$(dirname "$0")/.."
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST=${BACKUP_DIR:-/opt/ovd-backups}
KEEP_DAYS=${KEEP_DAYS:-14}
mkdir -p "$DEST"

# sqlite3's online backup API gives a consistent copy while the app keeps writing (WAL mode).
docker compose exec -T api python - <<'PY'
import glob, os, sqlite3
os.makedirs("/data/backup", exist_ok=True)
for path in glob.glob("/data/db/*.db") + glob.glob("/data/jobs/*.db"):
    out = os.path.join("/data/backup", os.path.basename(path))
    src, dst = sqlite3.connect(path), sqlite3.connect(out + ".tmp")
    with dst:
        src.backup(dst)
    src.close(); dst.close()
    os.replace(out + ".tmp", out)
    print("backed up", path)
PY
docker compose cp api:/data/backup "$DEST/ovd-$STAMP"
tar -czf "$DEST/ovd-$STAMP.tar.gz" -C "$DEST" "ovd-$STAMP" && rm -rf "$DEST/ovd-$STAMP"
find "$DEST" -name 'ovd-*.tar.gz' -mtime +"$KEEP_DAYS" -delete
echo "backup ok: $DEST/ovd-$STAMP.tar.gz"
