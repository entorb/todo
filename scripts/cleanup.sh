#!/bin/sh
set -e
cd "$(dirname "$0")/.."

rm -f .DS_Store .cspellcache backend/.coverage backend/coverage.xml frontend/.eslintcache
rm -rf backend/.ruff_cache frontend/coverage frontend/dist
