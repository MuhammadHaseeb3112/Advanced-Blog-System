#!/usr/bin/env bash
# Dump the blog database to ~/backups/blog (gzip, owner-only) and keep 14 days.
#   bash ~/blog/deploy/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DEST="$HOME/backups/blog"
mkdir -p "$DEST" && chmod 700 "$DEST"
umask 077
FILE="$DEST/blog-$(date +%Y%m%d-%H%M).sql.gz"
docker compose -p blog -f deploy/compose.prod.yml --env-file deploy/.env.prod \
  exec -T blog-db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip > "$FILE"
find "$DEST" -name 'blog-*.sql.gz' -mtime +14 -delete
echo "Saved $FILE"
