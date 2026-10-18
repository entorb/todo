# Helper Scripts

- `chk_*.sh` — code checks. exit 1 on failure. Slightly different from CI ([check.yml](../.github/workflows/check.yml)): here allowed to modify files. Non verbose output.
- `run_*.sh` — standalone use (start servers, run tools interactively).
- Backend CLI (`create_board`, `delete_board`, `set_user_secret`): `cd backend && uv run python -m scripts.<name>`
- [run_checks.sh](run_checks.sh) — runs all `chk_*.sh` scripts, reports failures.
