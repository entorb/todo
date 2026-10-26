# Todo

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=entorb_todo&metric=ncloc)](https://sonarcloud.io/summary/overall?id=entorb_todo)
[![Security issues](https://sonarcloud.io/api/project_badges/measure?project=entorb_todo&metric=software_quality_security_issues)](https://sonarcloud.io/summary/overall?id=entorb_todo)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=entorb_todo&metric=coverage)](https://sonarcloud.io/summary/overall?id=entorb_todo)

My TODO board: boards → columns → cards, labels, prio, revive cards, drag & drop, sort, bulk edit, export (txt / markdown / html to clipboard).

Built with:

- Backend: Python, [FastAPI](https://fastapi.tiangolo.com), [SQLModel](https://sqlmodel.tiangolo.com), SQLite — [backend/](backend/)
- Frontend: TypeScript, Vue 3, Vite, [Quasar](https://quasar.dev), Pinia — [frontend/](frontend/)

Setup, scripts and architecture: [AGENTS.md](AGENTS.md). Deployment: [deployment.md](deployment.md).

## Code checks

- Many tools for code checks are used in this repo, see GH Action [check.yml](.github/workflows/check.yml) and [script/](scripts/) for local running of `scripts/chk_*.sh`, run all via [scripts/run_checks.sh](scripts/run_checks.sh).
- [SonarQube](https://sonarcloud.io/summary/overall?id=entorb_timer)

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/overall?id=entorb_todo)
