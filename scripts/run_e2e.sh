#!/bin/sh
set -e
cd "$(dirname "$0")/../frontend"

# drop unused pages, also on test failure
trap 'sqlite3 ../backend/db-e2e.sqlite "VACUUM;"' EXIT

# Playwright webServer starts FastAPI (own e2e DB + secret) and Vite on its own.
pnpm run pw:run
