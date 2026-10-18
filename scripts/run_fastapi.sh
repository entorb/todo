#!/bin/sh
set -e
cd "$(dirname "$0")/../backend"

# --host localhost -> only listen for requests from local machine.
uv run --no-build uvicorn app.main:app --host localhost --port 9003 --reload
