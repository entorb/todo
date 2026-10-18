#!/bin/sh
set -e
cd "$(dirname "$0")/.."

FASTAPI_PID=""

cleanup() {
  [ -n "$FASTAPI_PID" ] && kill "$FASTAPI_PID" 2>/dev/null || true
}
trap cleanup EXIT

# start FastAPI if not already running
if ! curl -sf localhost:9003/openapi.json >/dev/null 2>&1; then
  (cd backend && uv run --no-build uvicorn app.main:app --host localhost --port 9003) &
  FASTAPI_PID=$!
  i=0
  until curl -sf localhost:9003/openapi.json >/dev/null 2>&1; do
    i=$((i + 1))
    [ "$i" -ge 20 ] && {
      echo "ERROR: uvicorn failed to start" >&2
      exit 1
    }
    sleep 0.5
  done
fi

cd frontend
rm -f openapi-ts-error-*.log
pnpm exec openapi-ts
