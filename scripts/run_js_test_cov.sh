#!/bin/sh
set -e
cd "$(dirname "$0")/../frontend"

pnpm exec vitest --watch=false --silent --coverage
