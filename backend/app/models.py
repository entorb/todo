"""
SQLModel definitions for the Nice TODO.

Uses Relationship() for parent-child associations with cascade deletes
so Board.columns and Column.cards load and delete automatically.
"""

from datetime import UTC, datetime

from pydantic import NaiveDatetime
from sqlalchemy import Index, func, text
from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    """Return current time as naive UTC datetime (safe for SQLite storage)."""
    return datetime.now(tz=UTC).replace(tzinfo=None)


class Label(SQLModel, table=True):
    """A global tag with name and color, shared across all boards."""

    __tablename__ = "label"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="", nullable=False)
    color: str = Field(default="#cccccc", nullable=False)


class Card(SQLModel, table=True):
    """A task item within a column."""

    __tablename__ = "card"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    column_id: int = Field(
        foreign_key="column_.id", ondelete="CASCADE", nullable=False, index=True
    )
    title: str = Field(default="", nullable=False)
    # ponytail: not UNIQUE(column_id, position) — the swap-based reorder writes
    # positions one-by-one in a single txn, which a unique constraint would reject.
    # Duplicate positions are possible after concurrent writes; order_by(position)
    # alone is then non-deterministic. Upgrade path: deferrable unique constraint
    # + batch position assignment (single UPDATE ... CASE).
    position: int = Field(default=0, nullable=False)
    is_revive: bool = Field(
        default=False,
        nullable=False,
        sa_column_kwargs={"server_default": "0"},
    )
    label_id: int | None = Field(
        default=None, foreign_key="label.id", ondelete="SET NULL", index=True
    )
    prio: bool | None = Field(default=None, nullable=True)
    date_created: NaiveDatetime = Field(default_factory=utcnow, nullable=False)
    date_completed: NaiveDatetime | None = Field(default=None, nullable=True)

    @property
    def is_completed(self) -> bool:
        """Card is completed when date_completed is set."""
        return self.date_completed is not None


class Column(SQLModel, table=True):
    """A named vertical list within a board."""

    __tablename__ = "column_"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    board_id: int = Field(
        foreign_key="board.id", ondelete="CASCADE", nullable=False, index=True
    )
    name: str = Field(default="", nullable=False)
    position: int = Field(default=0, nullable=False)

    cards: list[Card] = Relationship(
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Card.position"},
    )


class User(SQLModel, table=True):
    """A user owning boards."""

    __tablename__ = "user"  # type: ignore[assignment]
    # user names are unique case-insensitively (board member lookup by name)
    __table_args__ = (
        Index("ux_user_name_lower", func.lower(text("name")), unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    # nullable: no hash yet, successor app sets it
    secret_hashed: str | None = Field(default=None, unique=True, nullable=True)


class Board(SQLModel, table=True):
    """The top-level entity containing columns."""

    __tablename__ = "board"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    key: str = Field(unique=True, nullable=False, default="", index=True)
    name: str = Field(default="", nullable=False)
    last_login: NaiveDatetime | None = Field(default=None, nullable=True)

    columns: list[Column] = Relationship(
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Column.position"},
    )
    members: list["BoardMember"] = Relationship(cascade_delete=True)


class BoardMember(SQLModel, table=True):
    """User with card access (no board/column management) to a board."""

    __tablename__ = "board_member"  # type: ignore[assignment]

    board_id: int = Field(foreign_key="board.id", ondelete="CASCADE", primary_key=True)
    user_id: int = Field(
        foreign_key="user.id", ondelete="CASCADE", primary_key=True, index=True
    )


# API schemas


class LoginRequest(SQLModel):
    """Login with secret only (user is identified by secret)."""

    secret: str = Field(min_length=1)


class TokenResponse(SQLModel):
    """JWT access token."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


class UserInfo(SQLModel):
    """Authenticated user, from JWT."""

    user_id: int
    user_name: str


class LabelIn(SQLModel):
    """Create or update a label."""

    name: str = Field(min_length=1)
    color: str


class LabelPublic(SQLModel):
    """Label as returned by the API."""

    id: int
    name: str
    color: str


class CardPublic(SQLModel):
    """Card as returned by the API."""

    id: int
    column_id: int
    title: str
    position: int
    is_revive: bool
    label_id: int | None
    prio: bool | None
    date_created: NaiveDatetime
    date_completed: NaiveDatetime | None


class ColumnPublic(SQLModel):
    """Column incl. its cards."""

    id: int
    board_id: int
    name: str
    position: int
    cards: list[CardPublic]


class ColumnSummary(SQLModel):
    """Column without cards."""

    id: int
    name: str


class BoardSummary(SQLModel):
    """Board incl. column names, for switcher and move/copy."""

    id: int
    key: str
    name: str
    is_owner: bool = True
    columns: list[ColumnSummary]


class BoardPublic(SQLModel):
    """Board incl. columns and cards."""

    id: int
    key: str
    name: str
    last_login: NaiveDatetime | None
    is_owner: bool = True
    columns: list[ColumnPublic]


class BoardCreate(SQLModel):
    """Create a board. Key defaults to lowercased name."""

    name: str = Field(min_length=1)
    key: str | None = None


class BoardUpdate(SQLModel):
    """Rename board and/or change its key."""

    name: str | None = Field(default=None, min_length=1)
    key: str | None = None


class ColumnCreate(SQLModel):
    """Create a column at the end of a board."""

    board_id: int


class ColumnUpdate(SQLModel):
    """Rename a column."""

    name: str = Field(min_length=1)


class IdList(SQLModel):
    """Ordered list of ids, e.g. new column order."""

    ids: list[int]


class CardCreate(SQLModel):
    """Create a card at the end of a column."""

    column_id: int
    title: str = Field(min_length=1)


class CardUpdate(SQLModel):
    """Partial card update. Explicit null for prio/label_id unsets them."""

    title: str | None = Field(default=None, min_length=1)
    is_completed: bool | None = None
    is_revive: bool | None = None
    prio: bool | None = None
    label_id: int | None = None


class CardBulkUpdate(SQLModel):
    """Same update for many cards. Explicit null for prio/label_id unsets them."""

    ids: list[int] = Field(min_length=1)
    is_revive: bool | None = None
    prio: bool | None = None
    label_id: int | None = None


class CardMove(SQLModel):
    """Target of a card move or copy. Position defaults to end of column."""

    column_id: int
    position: int | None = None


class ExportResponse(SQLModel):
    """Exported board text."""

    text: str


class CountResponse(SQLModel):
    """Number of affected rows."""

    count: int
