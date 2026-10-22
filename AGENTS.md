# AGENTS.md

Kanban todo boards. FastAPI + SQLModel backend and Vue 3 + Quasar frontend. Structure and auth follow korrekturleser.

- Backend details: [backend/AGENTS.md](backend/AGENTS.md)
- Frontend details: [frontend/AGENTS.md](frontend/AGENTS.md)

instead of `/tmp/` use `./tmp/` dir for helper scripts.

## Dev setup

```sh
(cd backend && uv sync && cp .env.example .env)  # set JWT_SECRET_KEY (>= 32 chars)
# uv workspace: uv.lock + .venv at root, backend = member
pnpm install  # pnpm workspace: lockfile + store at root, frontend/node_modules = symlinks
(cd backend && uv run python -m scripts.set_user_secret 1)  # login secret of user 1
```

Startup creates/migrates `backend/sqlite.db`. No secret is ever seeded, users without `secret_hashed` cannot log in. Prod detection: `/home/entorb/todo` exists.

## Run apps

| App | Script | URL |
| --- | ------ | --- |
| FastAPI (BE) | `scripts/run_fastapi.sh` | `localhost:9003/docs` |
| Vue.js (FE) | `scripts/run_vue.sh` | `localhost:5173/todo/` |

## API code generation

```sh
scripts/gen_api_for_vue.sh  # starts uvicorn on :9003 if not running
```

Generates `frontend/src/client/` via `@hey-api/openapi-ts` (operation names = FastAPI route function names). Auto-generated — DO NOT edit manually. Rerun after every API change.

## Feature workflow (full stack)

1. BE: schema in `models.py` → logic in `crud.py` → route in `api/routes/` → test in `backend/tests/`
2. `scripts/gen_api_for_vue.sh`
3. FE: call generated fn in `stores/board.ts` (via `run()`) → component / dialog
4. Checks (below)

## Checks

Each `chk_*.sh` prints `OK` on success (no errors found), or failure output + non-zero exit.

run after each modification

- Python: `scripts/chk_py_lint.sh` (ruff format + fix)
- JavaScript: `scripts/chk_js_format.sh` (biome)

run before committing

- `scripts/run_checks.sh` (runs all `chk_*.sh` sequentially: lint, types, dead code, tests, audit, pre-commit)
- `scripts/run_e2e.sh` (Playwright)

If a check fails → fix → rerun that check only → repeat → final `scripts/run_checks.sh`.

| Check | Python | JavaScript |
| ----- | ------ | ---------- |
| format/lint | `chk_py_lint.sh` (ruff) | `chk_js_format.sh` (biome), `chk_js_lint.sh` (eslint) |
| types | `chk_py_types.sh` (pyright) | `chk_js_types.sh` (vue-tsc) |
| dead code | `chk_py_dead.sh` (vulture) | `chk_js_dead.sh` (knip) |
| tests | `chk_py_test.sh` (pytest) | `chk_js_test.sh` (vitest) |
| audit | `chk_py_package_audit.sh` | `chk_js_package_audit.sh` |

To re-run a single failing test:

- Python: `cd backend && uv run pytest tests/test_file.py::test_function`
- JavaScript: `cd frontend && pnpm exec vitest path/to/test.spec.ts`

### Add CSpell findings

If `scripts/run_spelling.sh` finds unknown words, these are written to `cspell-words-missing.txt`. The correct ones shall be appended to `cspell-words.txt`, which is sorted by `scripts/chk_pre-commit.sh`.

## Architecture

- **`backend/`** — FastAPI at root path `/be/todo`, SQLite via SQLModel. Routers: auth, boards, columns, cards, labels.
- **`frontend/`** — Vue 3 + Quasar + Pinia + TypeScript, served at `/todo/`.
- **`scripts/`** — run / check / deploy shell scripts, all callable from any cwd.

### Auth

Same as korrekturleser: `POST /api/auth/login {secret}` → bcrypt check against all `user.secret_hashed` → HS256 JWT (1 year) → FE stores in localStorage, sends `Authorization: Bearer`. Login rate limit 5/min per IP (PROD only). FE logs out on any 401.

### Ownership

Every board / column / card access goes through `crud.get_board|get_column|get_card` with `owner_id` from JWT → foreign data is 404. Labels are global.

### Errors

`crud.NotFoundError` → 404, `crud.ConflictError` (validation, duplicates) → 409 with `detail` message, shown by FE as notify.

## Testing

| Stack | Command | Notes |
| ----- | ------- | ----- |
| Python | `scripts/chk_py_test.sh` | fresh tmp DB per test, users 1 (secret `test`) and 2 (secret `other`) |
| Python + coverage | `scripts/run_py_test_cov.sh` | |
| Vue | `scripts/chk_js_test.sh` | vitest, jsdom |
| Vue + coverage | `scripts/run_js_test_cov.sh` | |
| E2E | `scripts/run_e2e.sh` | own DB `backend/sqlite-e2e.db`, seeded by `frontend/e2e/global-setup.ts` |

## Deployment

Target: Uberspace. Script: `scripts/deploy.sh`. Prod under gunicorn, see [deployment.md](deployment.md).

## SonarCloud

Issues: `https://sonarcloud.io/project/issues?id=entorb_todo`, fetch via `scripts/get_sonar_issues.sh`.
