#!/bin/sh
set -e
cd "$(dirname "$0")/../backend"

# consistent snapshot via sqlite3 backup API
ssh entorb@entorb.net "cd be/todo && python3.14 -c \"import sqlite3; s=sqlite3.connect('db.sqlite'); d=sqlite3.connect('db-snapshot.sqlite'); s.backup(d); d.close(); s.close()\""
scp entorb@entorb.net:be/todo/db-snapshot.sqlite ./db.sqlite
ssh entorb@entorb.net "rm be/todo/db-snapshot.sqlite"
echo "downloaded to backend/db.sqlite"
