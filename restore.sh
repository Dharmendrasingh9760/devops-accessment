#!/bin/sh
# Restore a backup produced by backup.sh
# Usage: ./restore.sh /backups/appdb_2026-06-26_02-00-00.sql.gz

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

echo "WARNING: this will overwrite the current contents of database ${POSTGRES_DB}."
echo "Press Ctrl+C within 5 seconds to cancel."
sleep 5

gunzip -c "$BACKUP_FILE" | psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "Restore complete."
