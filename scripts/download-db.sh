#!/bin/sh
set -e
cd "$(dirname "$0")/../backend"

# consistent snapshot of the WAL-mode DB via sqlite3 backup API
ssh entorb@entorb.net "cd be/todo && python3.11 -c \"import sqlite3; s=sqlite3.connect('sqlite.db'); d=sqlite3.connect('sqlite-snapshot.db'); s.backup(d); d.close(); s.close()\""
scp entorb@entorb.net:be/todo/sqlite-snapshot.db ./sqlite.db
ssh entorb@entorb.net "rm be/todo/sqlite-snapshot.db"
echo "downloaded to backend/sqlite.db"
