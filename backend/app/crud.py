"""
DB access layer.

All text inputs are stripped of white spaces prior to insert/update.
Every lookup is scoped to the owner or board members, foreign data raises
NotFoundError. Board and column management is owner-only, cards are member-allowed.
"""

import re
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy import ColumnElement, case, func, or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import selectinload  # type: ignore[attr-defined]
from sqlmodel import Session, SQLModel, col, delete, select, update

from app.core.db import get_engine
from app.models import Board, BoardMember, Card, Column, Label, User, utcnow
from app.sort import card_sort_by_date, card_sort_by_prio_label_name

_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9._~-]+$")
_COLOR_PATTERN = re.compile(r"^#[0-9a-f]{6}$")
COMPLETED_CUTOFF_DAYS = 14


class NotFoundError(LookupError):
    """Entity missing or owned by someone else (-> 404)."""


class ConflictError(ValueError):
    """Validation error, e.g. duplicate name (-> 409)."""


def _clean_title(title: str) -> str:
    """Normalize title by stripping whitespace and collapsing multiple spaces."""
    # CRLF to LF
    title = title.replace("\r\n", "\n")
    # drop multiple spaces, but keep line breaks
    title = re.sub(r"[ \t]+", " ", title)
    return title.strip()


# Setup


def init_db() -> None:
    """Create all tables if they don't exist, and run migrations."""
    engine = get_engine()
    try:
        SQLModel.metadata.create_all(engine)
    except OperationalError:
        # parallel gunicorn workers race on a fresh DB; the retry sees the tables
        SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    """
    Run explicit schema/data migrations on every startup.

    Add future migrations here as discrete, idempotent steps.
    No secret is set here, see scripts/set_user_secret.py
    """
    engine = get_engine()
    with Session(engine) as s:
        if s.get(User, 1) is None:
            s.add(User(id=1, name="Torben"))
            s.commit()


# Users


def get_user_by_secret(
    s: Session, secret: str, verify: Callable[[str, str], bool]
) -> User | None:
    """
    Return the user whose secret matches.

    Checks all hashes without early exit, so response time does not reveal
    which/how many users exist before the match.
    ponytail: O(users) bcrypt checks per login, fine for a handful of users.
    """
    found = None
    users = s.exec(select(User).where(col(User.secret_hashed).is_not(None))).all()
    for user in users:
        if verify(secret, user.secret_hashed or "") and found is None:
            found = user
    return found


def get_user_by_name(s: Session, name: str) -> User | None:
    """Return the user with this name (case-insensitive)."""
    return s.exec(
        select(User).where(func.lower(User.name) == name.strip().lower())
    ).first()


# Ownership lookups


def _board_access(user_id: int) -> ColumnElement[bool]:
    """Condition: user owns the board or is a member (no join, no duplicates)."""
    return or_(
        col(Board.owner_id) == user_id,
        col(Board.id).in_(
            select(BoardMember.board_id).where(BoardMember.user_id == user_id)
        ),
    )


def get_board(
    s: Session, owner_id: int, board_id: int, *, owner_only: bool = True
) -> Board:
    """Return board, owner-only unless told otherwise, or raise NotFoundError."""
    board = s.get(Board, board_id)
    if board is None:
        raise NotFoundError
    if board.owner_id != owner_id and (
        owner_only or s.get(BoardMember, (board_id, owner_id)) is None
    ):
        raise NotFoundError
    return board


def get_board_by_key(s: Session, owner_id: int, key: str) -> Board:
    """Load accessible board with columns and cards eagerly loaded."""
    # ponytail: selectinload fetches every card on every page load; fine for
    # personal boards. Upgrade path: per-column lazy load or pagination.
    board = s.exec(
        select(Board)
        .where(Board.key == key, _board_access(owner_id))
        .options(selectinload(Board.columns).selectinload(Column.cards))  # type: ignore[arg-type]
    ).first()
    if board is None:
        raise NotFoundError
    return board


def get_column(
    s: Session, owner_id: int, column_id: int, *, owner_only: bool = True
) -> Column:
    """Return column, owner-only unless told otherwise, or raise NotFoundError."""
    access = col(Board.owner_id) == owner_id if owner_only else _board_access(owner_id)
    column = s.exec(
        select(Column).join(Board).where(Column.id == column_id, access)
    ).first()
    if column is None:
        raise NotFoundError
    return column


def get_card(s: Session, owner_id: int, card_id: int) -> Card:
    """Return card on an accessible board or raise NotFoundError."""
    card = s.exec(
        select(Card)
        .join(Column)
        .join(Board)
        .where(Card.id == card_id, _board_access(owner_id))
    ).first()
    if card is None:
        raise NotFoundError
    return card


def check_cards_owned(s: Session, owner_id: int, card_ids: list[int]) -> None:
    """Raise NotFoundError unless all cards are on accessible boards."""
    owned = s.exec(
        select(Card.id)
        .join(Column)
        .join(Board)
        .where(col(Card.id).in_(card_ids), _board_access(owner_id))
    ).all()
    if set(owned) != set(card_ids):
        raise NotFoundError


# Board


def touch_last_login(s: Session, board: Board) -> None:
    """Record the board's last_login timestamp."""
    board.last_login = utcnow()
    s.add(board)
    s.commit()


def get_boards_with_columns(s: Session, owner_id: int) -> list[Board]:
    """Return accessible boards (owned or member) with columns, no cards."""
    return list(
        s.exec(
            select(Board)
            .where(_board_access(owner_id))
            .options(selectinload(Board.columns))  # type: ignore[arg-type]
            .order_by(Board.name)
        ).all()
    )


def _validate_board_key(s: Session, key: str, exclude_id: int | None = None) -> None:
    """Raise ConflictError if key is invalid or taken."""
    if not key:
        msg = "Board key must not be empty"
        raise ConflictError(msg)
    if not _KEY_PATTERN.match(key):
        msg = "Board key contains invalid characters"
        raise ConflictError(msg)
    existing_id = s.exec(select(Board.id).where(Board.key == key)).first()
    if existing_id is not None and existing_id != exclude_id:
        msg = "Board key must be unique"
        raise ConflictError(msg)


def add_board(s: Session, owner_id: int, key: str, name: str) -> Board:
    """Create a new board."""
    key_clean = key.strip().lower()
    _validate_board_key(s, key_clean)
    board = Board(owner_id=owner_id, key=key_clean, name=name.strip())
    board.last_login = utcnow()
    s.add(board)
    try:
        s.commit()
    except IntegrityError as e:
        s.rollback()
        msg = "Board key must be unique"
        raise ConflictError(msg) from e
    s.refresh(board)
    return board


def add_board_member(s: Session, board: Board, user_id: int) -> None:
    """Grant a user card access to the board (idempotent)."""
    board_id = board.id
    assert board_id is not None
    if s.get(BoardMember, (board_id, user_id)) is None:
        s.add(BoardMember(board_id=board_id, user_id=user_id))
        s.commit()


def update_board(s: Session, board: Board, name: str | None, key: str | None) -> Board:
    """Rename the board and/or change its URL key."""
    if key is not None:
        key_clean = key.strip().lower()
        _validate_board_key(s, key_clean, exclude_id=board.id)
        board.key = key_clean
    if name is not None:
        board.name = name.strip()
    s.add(board)
    s.commit()
    s.refresh(board)
    return board


def delete_board(s: Session, board: Board) -> None:
    """Delete board and all associated data (cascades via relationships)."""
    s.delete(board)
    s.commit()


# Columns


def _get_columns(s: Session, board_id: int) -> list[Column]:
    return list(
        s.exec(
            select(Column)
            .where(Column.board_id == board_id)
            .order_by(col(Column.position))
        ).all()
    )


def create_column(s: Session, board_id: int) -> Column:
    """Create a new column with unique default name at end."""
    existing = _get_columns(s, board_id)
    name = "New Column"
    names = {c.name for c in existing}
    if name in names:
        i = 2
        while f"{name} {i}" in names:
            i += 1
        name = f"{name} {i}"
    column = Column(board_id=board_id, name=name, position=len(existing))
    s.add(column)
    s.commit()
    s.refresh(column)
    return column


def update_column_name(s: Session, column: Column, name: str) -> Column:
    """Rename a column, names are unique per board."""
    name = name.strip()
    for other in _get_columns(s, column.board_id):
        if other.id != column.id and other.name == name:
            msg = f"Column name '{name}' already exists"
            raise ConflictError(msg)
    column.name = name
    s.add(column)
    s.commit()
    s.refresh(column)
    return column


def update_column_order(s: Session, board: Board, column_ids: list[int]) -> None:
    """Set column positions from ordered id list (must be the board's columns)."""
    existing = {c.id for c in _get_columns(s, board.id)}  # type: ignore[arg-type]
    if set(column_ids) != existing or len(column_ids) != len(existing):
        raise NotFoundError
    for pos, col_id in enumerate(column_ids):
        s.exec(update(Column).where(col(Column.id) == col_id).values(position=pos))
    s.commit()


def delete_column(s: Session, column: Column) -> None:
    """Delete column and its cards (cascades via relationship)."""
    s.delete(column)
    s.commit()


# Cards


def _get_cards(s: Session, column_id: int) -> list[Card]:
    return list(
        s.exec(
            select(Card)
            .where(Card.column_id == column_id)
            .order_by(col(Card.position), col(Card.id))
        ).all()
    )


def create_card(s: Session, column_id: int, title: str) -> Card:
    """Create a new card at the end of the column."""
    position = len(_get_cards(s, column_id))
    card = Card(column_id=column_id, title=_clean_title(title), position=position)
    s.add(card)
    s.commit()
    s.refresh(card)
    return card


def update_card(s: Session, card: Card, data: dict) -> Card:
    """Partial update, data from CardUpdate.model_dump(exclude_unset=True)."""
    if "title" in data and data["title"] is not None:
        title = _clean_title(data["title"])
        if title:
            card.title = title
    if "is_completed" in data and data["is_completed"] is not None:
        card.date_completed = utcnow() if data["is_completed"] else None
    if "is_revive" in data and data["is_revive"] is not None:
        card.is_revive = data["is_revive"]
    if "prio" in data:
        card.prio = data["prio"]
    if "label_id" in data:
        card.label_id = data["label_id"]
    s.add(card)
    s.commit()
    s.refresh(card)
    return card


def _renumber(cards: list[Card]) -> None:
    for idx, c in enumerate(cards):
        c.position = idx


def move_card(
    s: Session, card: Card, target_column_id: int, position: int | None
) -> Card:
    """Move card to column/position, renumber source and target columns."""
    source_column_id = card.column_id
    source = [c for c in _get_cards(s, source_column_id) if c.id != card.id]
    target = (
        source
        if target_column_id == source_column_id
        else _get_cards(s, target_column_id)
    )
    pos = len(target) if position is None else max(0, min(position, len(target)))
    target.insert(pos, card)
    card.column_id = target_column_id
    _renumber(source)
    _renumber(target)
    s.add_all([*source, *target])
    s.commit()
    s.refresh(card)
    return card


def copy_card(s: Session, card: Card, target_column_id: int) -> Card:
    """Copy a card to the end of the target column."""
    new_card = Card(
        column_id=target_column_id,
        title=card.title,
        position=len(_get_cards(s, target_column_id)),
        label_id=card.label_id,
        is_revive=card.is_revive,
        prio=card.prio,
    )
    s.add(new_card)
    s.commit()
    s.refresh(new_card)
    return new_card


def delete_card(s: Session, card: Card) -> None:
    """Delete a single card."""
    s.delete(card)
    s.commit()


def bulk_update_cards(s: Session, card_ids: list[int], data: dict) -> None:
    """Set is_revive / prio / label_id on many cards with one UPDATE."""
    values = {k: v for k, v in data.items() if k in {"is_revive", "prio", "label_id"}}
    if values.get("is_revive", True) is None:
        del values["is_revive"]
    if values:
        s.exec(update(Card).where(col(Card.id).in_(card_ids)).values(**values))
        s.commit()


# Bulk delete


def _delete_conditions(mode: str) -> tuple[list, bool]:
    """Return (extra where conditions, reset_repeats) for a delete mode."""
    if mode == "completed":
        return [col(Card.date_completed).is_not(None)], True
    if mode == "2w":
        cutoff = utcnow() - timedelta(days=COMPLETED_CUTOFF_DAYS)
        return [
            col(Card.date_completed).is_not(None),
            col(Card.date_completed) < cutoff,
        ], False
    return [], True  # all


def _board_column_ids(s: Session, board_id: int) -> list[int]:
    return [c.id for c in _get_columns(s, board_id) if c.id is not None]


def get_deletable_cards(s: Session, board_id: int, mode: str) -> list[Card]:
    """Preview: non-revive cards a delete with this mode would remove."""
    col_ids = _board_column_ids(s, board_id)
    conditions, _ = _delete_conditions(mode)
    return list(
        s.exec(
            select(Card)
            .where(
                col(Card.column_id).in_(col_ids),
                col(Card.is_revive).is_(False),
                *conditions,
            )
            .order_by(col(Card.column_id), col(Card.position))
        ).all()
    )


def delete_cards(s: Session, board_id: int, mode: str) -> int:
    """Delete non-revive cards per mode, optionally reset revive cards."""
    col_ids = _board_column_ids(s, board_id)
    if not col_ids:
        return 0
    conditions, reset_repeats = _delete_conditions(mode)
    result = s.exec(
        delete(Card).where(
            col(Card.column_id).in_(col_ids),
            col(Card.is_revive).is_(False),
            *conditions,
        )
    )
    count = result.rowcount or 0
    if reset_repeats:
        s.exec(
            update(Card)
            .where(col(Card.column_id).in_(col_ids), col(Card.is_revive).is_(True))
            .values(date_completed=None)
        )
    s.commit()
    return count


# Sorting


def sort_cards(s: Session, board: Board, by: str) -> None:
    """Sort cards per column by 'prio' (prio, label, title) or 'date'."""
    if by == "date":
        key_fn: Callable[[Card], tuple] = card_sort_by_date()
    else:
        label_map = {lb.id: (lb.name or "") for lb in get_labels(s)}
        key_fn = card_sort_by_prio_label_name(label_map)
    for column in board.columns:
        cards = sorted(column.cards, key=key_fn)
        if not cards:
            continue
        whens = [(Card.id == c.id, idx) for idx, c in enumerate(cards)]
        s.exec(
            update(Card)
            .where(col(Card.column_id) == column.id)
            .values(position=case(*whens, else_=Card.position))  # type: ignore[arg-type]
        )
    s.commit()


# Labels
# ponytail: labels are global, shared by all users.
# Upgrade path: label.owner_id + scope these functions.


def get_labels(s: Session) -> list[Label]:
    """Get all labels."""
    return list(s.exec(select(Label).order_by(Label.name)).all())


def get_label(s: Session, label_id: int) -> Label:
    """Return label or raise NotFoundError."""
    label = s.get(Label, label_id)
    if label is None:
        raise NotFoundError
    return label


def _validate_label(
    s: Session, name: str, color: str, exclude_label_id: int | None = None
) -> None:
    """Raise ConflictError if name or color is invalid/duplicate."""
    if not _COLOR_PATTERN.fullmatch(color):
        msg = f"Invalid color format: '{color}' (expected #rrggbb)"
        raise ConflictError(msg)
    for lbl in get_labels(s):
        if lbl.id == exclude_label_id:
            continue
        if lbl.name == name:
            msg = f"Label name '{name}' already exists"
            raise ConflictError(msg)
        if lbl.color.lower() == color:
            msg = f"Label color '{color}' already in use"
            raise ConflictError(msg)


def save_label(s: Session, label: Label, name: str, color: str) -> Label:
    """Validate and insert/update a label."""
    name_clean = name.strip()
    color_clean = color.strip().lower()
    _validate_label(s, name_clean, color_clean, exclude_label_id=label.id)
    label.name = name_clean
    label.color = color_clean
    s.add(label)
    s.commit()
    s.refresh(label)
    return label


def delete_label(s: Session, label: Label) -> None:
    """Delete a label; cards' label_id is nulled via FK ON DELETE SET NULL."""
    s.delete(label)
    s.commit()
