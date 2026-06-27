#!/bin/sh
# Run inside the db container or via `docker exec`.
# Usage: ./backup.sh
# Produces a timestamped, gzip-compressed SQL dump in /backups (mount this
# as a volume on the host so backups survive container recreation).

set -e

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "Backup written to ${BACKUP_DIR}/${FILENAME}"

# Retention: keep the last 7 daily backups, delete anything older
find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" -mtime +7 -delete
