#!/bin/sh
set -e
cd "$(dirname "$0")/.."

# cleanup
rm -f .DS_Store
rm -f -- ./*/.DS_Store

echo "## Code Gen and Checks"
echo "### Gen API code"
./scripts/gen_api_for_vue.sh

echo "### Spelling"
./scripts/run_spelling.sh

echo "### Code checks"
./scripts/run_checks.sh

echo "### E2E tests"
./scripts/run_e2e.sh

echo "## Frontend Build and Transfer"
(cd frontend && pnpm run build)
rsync -rhv --delete --no-perms frontend/dist/ entorb@entorb.net:html/todo/

echo "## Backend"
(cd backend && uv run --no-build python -m scripts.gen_requirements)
rsync -hvz --no-perms backend/requirements.txt entorb@entorb.net:be/todo/
# DO NOT sync the .env secret file
rsync -rhvz --delete --delete-excluded --no-perms --exclude __pycache__ backend/app/ entorb@entorb.net:be/todo/app/
rsync -rhvz --delete --delete-excluded --no-perms --exclude __pycache__ backend/scripts/ entorb@entorb.net:be/todo/scripts/

echo "### Install packages"
ssh entorb@entorb.net "pip3.11 install --user -r be/todo/requirements.txt > /dev/null"

echo "### Restart fastapi"
ssh entorb@entorb.net "supervisorctl restart fastapi-todo"

echo "## DONE"
