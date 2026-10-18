#!/bin/sh
set -e
cd "$(dirname "$0")/.."

(
  cd backend
  uv lock --upgrade
  uv sync --no-build --upgrade
  # extract package info to requirements.txt
  uv run --no-build python -m scripts.gen_requirements
)

pnpm install --ignore-scripts
