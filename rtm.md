# Merge RTM features into todo
<!-- cspell:disable -->
## Context

User uses Remember the Milk (RTM) mainly for tasks with due date + "repeat after"; also needs url + estimate. Goal: cover these in todo instead of separate app. Sample RTM data in `tmp/test_data/`. Verdict: merge — auth, users, labels, prio, completed, deploy, checks, FE stack all reused; gap = few Card fields + due view + archive.

## RTM feature research (web)

- **Repeat "after"**: next instance only on completion; next due = completion + interval ("after 5 days"). RTM creates new task per instance (props copied) — see 3 rows "unit test 2: repeat" in `expected_tasks.json`.
- **Repeat "every"**: fixed schedule from due date; day/weekday/week/month/year, intervals, weekday sets, nth weekday, last day, until / for N times.
- Other: Smart Add one-line syntax, Smart Lists (~50 search operators), subtasks, sharing, reminders (email/SMS/push), integrations (Gmail, Calendar, Outlook, IFTTT, Zapier, MCP), mobile/offline, MilkScript. Free tier: completed archive 7 days only.
- In scope: due, repeat (after + simple every), prio, tags, completed, url, estimate, archive. Out: reminders, sharing, subtasks, integrations, Smart Add parser, full RRULE.

## Mapping RTM → todo

| RTM | todo | Note |
| --- | --- | --- |
| list | **open decision**, see below | |
| task name / completed | `Card.title` / `date_completed` | exists |
| tags | `Label` (global, 1 per card) | first tag only on import |
| priority 1/2/3/N | `prio: bool\|None` | 1 → True, else None (lossy) |
| due | `date_due` | new |
| rrule + every flag | `repeat` | new |
| url | `url` | new |
| estimate `PT1H30M` | `estimate_min: int` | new, ISO 8601 → minutes |
| deleted | `date_archived` | new, soft delete |
| notes, postponed, participants, location | — | skip |

### List mapping — undecided

- **list = board**: separate board per list; columns free (e.g. status). Due view across boards required anyway.
- **list = column**: one "RTM" board, lists as columns; Kanban drag between lists works.
- **list = label**: lists flatten into labels; only 1 label per card, collides with tags.
Data model below works for all three; only import script + due view differ. Decide before import script.

## Design

Backend `backend/app/models.py` `Card` (all nullable, no server default beyond NULL → added via existing startup migrate):

- `date_due: date | None`
- `repeat: str | None` — `"after 3d"`, `"every 1w"`, units `d|w|m|y`. "after" base = completion date, "every" base = old due. ponytail: no weekday sets / nth weekday / until; upgrade path = RRULE + `dateutil.rrule`.
- `url: str | None` — validate `^https?://` at API boundary (blocks `javascript:` links in FE).
- `estimate_min: int | None` (ge=0). FE shows `1h 30m`.
- `date_archived: NaiveDatetime | None` — soft delete.
- Existing `is_revive` (renamed from `is_repeat`; checklist-reset semantic, distinct from `repeat`).

`backend/app/crud.py`:

- update card (~line 329): on set `date_completed` with `repeat` → `date_due = base + interval`, `date_completed = None`. Month/year via `dateutil.relativedelta` if installed, else small month-add helper.
- validate `repeat` regex `^(after|every) \d+[dwmy]$` → `ConflictError` (409).
- **Archive instead of delete**: `delete_cards` (~line 437) + single-card delete → `UPDATE ... SET date_archived = now`. All card reads (board load via `Column.cards` relationship, `get_card`, bulk ops, `get_deletable_cards`) filter `date_archived IS NULL` — relationship needs `primaryjoin` with filter, grep every `select(Card)`. Column/board delete stays hard (cascade).
- Optional later: archive view + restore + purge-older-than-N.
- New `GET /api/cards/due?days=N`: owner's non-archived cards with `date_due`, all boards, sorted by due (join board.owner_id).
- `export_service.py`: include new fields.

Frontend:

- `TodoCard.vue`: due chip (red overdue, orange today), url icon link, estimate chip.
- Card edit dialog: date picker, repeat select (mode + n + unit), url, estimate.
- New "Due" page: flat list sorted by due, complete button.
- Store calls via `run()` in `stores/board.ts`.
- `DeleteCardsDialog.vue`: wording delete → archive.

Import script `backend/scripts/import_rtm.py`: RTM JSON export → cards per chosen list mapping; `rrule FREQ/INTERVAL` + `every` (0=after, 1=every) → `repeat`, unsupported RRULE parts warn + plain interval; `estimate` ISO → minutes; skip deleted; completed → `date_completed` (or skip).

## Verification

- pytest: repeat after/every shifts due correctly (incl. month end); bad repeat / non-http url → 409; archive hides card from board + due view, row still in DB; due view ownership (user 2 sees nothing of user 1).
- Import script: run against `tmp/test_data/`, assert vs `expected_tasks.json`.
- `scripts/gen_api_for_vue.sh`, `scripts/run_checks.sh`, `scripts/run_e2e.sh`.
- Manual: `scripts/run_fastapi.sh` + `scripts/run_vue.sh`; card with due + `after 1w`, complete → due +7d; delete → gone from board, present in DB.
