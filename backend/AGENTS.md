# Backend - Coding Guidelines

FastAPI + SQLModel + SQLite. Layout like full-stack-fastapi-template. Run all commands from `backend/` (`uv run ...`), or via `../scripts/*.sh`.

## Layout

| Path | Content |
| ---- | ------- |
| `app/main.py` | app, `root_path=/be/todo`, routers under `/api/*`, exception handlers, CORS, lifespan → `crud.init_db()` |
| `app/core/config.py` | pydantic-settings from `backend/.env`, `get_settings()` (lru_cache), PROD/Local detection, CORS origins |
| `app/core/db.py` | `get_engine()` (lru_cache, WAL, FK on), `get_session()` |
| `app/core/security.py` | bcrypt `hash_secret`, JWT `create_access_token` / `decode_token` |
| `app/api/deps.py` | `SessionDep`, `CurrentUser` (`UserInfo`), `limiter` (slowapi, PROD only) |
| `app/api/routes/` | `auth`, `boards`, `columns`, `cards`, `labels` — thin HTTP layer |
| `app/models.py` | tables (`label`, `card`, `column_`, `user`, `board`) + API schemas (`*Public`, `*Create`, `*Update`, ...) |
| `app/crud.py` | ALL DB access, validation, startup seed (`_migrate`) |
| `app/sort.py` | card sort keys, `app/export_service.py` markdown/JSON export |
| `scripts/` | CLI: `set_user_secret`, `create_board`, `delete_board`, ... (`uv run python -m scripts.<name>`) |
| `tests/` | pytest, `conftest.py` fixtures |

## Route pattern

```python
@router.patch("/{column_id}")
def update_column(
    column_id: int, data: ColumnUpdate, session: SessionDep, user: CurrentUser
) -> ColumnPublic:
    """Rename a column."""
    column = crud.get_column(session, user.user_id, column_id)  # ownership check
    column = crud.update_column_name(session, column, data.name)
    return ColumnPublic.model_validate(column, from_attributes=True)
```

- Function name = generated TS operation name (`generate_unique_id_function=route.name`) → pick clear, unique names.
- Return type annotation = response model. Create → `status_code=201`, delete → `204` + `Response`.
- No DB / business logic in routes, only `crud.*` calls.
- New decorator type (e.g. `@router.head`)? Add to `[tool.vulture] ignore_decorators` in `pyproject.toml`.

## crud.py

- Every board/column/card lookup via `get_board|get_column|get_card(session, owner_id, id)` → raises `NotFoundError` (404) if missing or foreign.
- Validation / duplicates → raise `ConflictError("user facing message")` (409). Do not raise `HTTPException` here.
- Strip text inputs (`_clean_title` for titles).
- Schema change → add idempotent step in `_migrate()` (runs every startup).

## Models

- Datetimes: naive UTC via `utcnow()`, annotate `NaiveDatetime` (not `datetime`, sqlmodel maps it to `UTCDateTime` which rejects naive values).
- Cascades via `ondelete="CASCADE"` + `Relationship`.

## Style

- Ruff (`../ruff.toml`) + pyright + vulture, see root checks.
- Docstring on every public function / route (short, one line).
- Mark deliberate shortcuts with `# ponytail:` comment (ceiling + upgrade path).

## Tests

- `tests/conftest.py`: autouse `_tmp_db` (fresh SQLite per test), fixtures `session`, `client` (`TestClient`), `auth_headers` (user 1, secret `test`), `other_headers` (user 2, secret `other`).
- `test_api.py` HTTP flows, `test_crud.py` crud directly, `test_auth.py`, `test_export_service.py`.
- New endpoint touching owned data → also assert `other_headers` gets 404.
- Single test: `uv run pytest tests/test_api.py::test_name`
