#!/bin/sh
set -e
cd "$(dirname "$0")/../backend"

uv run --no-build pytest --quiet --no-summary --tb=short --cov --cov-report=term-missing
