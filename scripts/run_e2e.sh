#!/bin/sh
set -e
cd "$(dirname "$0")/../frontend"

# Playwright webServer starts FastAPI (own e2e DB + secret) and Vite on its own.
pnpm run pw:run
