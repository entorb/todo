#!/bin/sh
set -e
cd "$(dirname "$0")/../backend"

echo "id owner key"
sqlite3 db.sqlite "SELECT id, owner_id, key FROM board ORDER BY id;"
