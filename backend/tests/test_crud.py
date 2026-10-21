from datetime import timedelta

import pytest
from app import crud
from app.core.security import hash_secret, verify_secret
from app.models import Board, BoardMember, Card, Label, User, utcnow
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select


def _board(s: Session, key: str = "b", owner_id: int = 1) -> Board:
    return crud.add_board(s, owner_id, key, key.upper())


def _cards(s: Session, column_id: int, *titles: str) -> list[Card]:
    return [crud.create_card(s, column_id, t) for t in titles]


def _titles(s: Session, column_id: int) -> list[str]:
    return [c.title for c in crud._get_cards(s, column_id)]  # noqa: SLF001


class TestBoard:
    def test_add_lowercases_key(self, session):
        board = crud.add_board(session, 1, " MyKey ", " Name ")
        assert (board.key, board.name) == ("mykey", "Name")
        assert board.last_login is not None

    @pytest.mark.parametrize(
        ("key", "msg"),
        [
            ("", "Board key must not be empty"),
            ("a b", "Board key contains invalid characters"),
            ("dup", "Board key must be unique"),
        ],
    )
    def test_add_invalid(self, session, key, msg):
        _board(session, "dup")
        with pytest.raises(crud.ConflictError, match=msg):
            crud.add_board(session, 1, key, "x")

    def test_update_key_own_and_duplicate(self, session):
        b1 = _board(session, "one")
        _board(session, "two")
        crud.update_board(session, b1, None, "ONE")
        assert b1.key == "one"
        with pytest.raises(crud.ConflictError):
            crud.update_board(session, b1, None, "two")

    def test_ownership(self, session):
        board = _board(session, "mine", owner_id=1)
        assert board.id is not None
        with pytest.raises(crud.NotFoundError):
            crud.get_board(session, 2, board.id)
        with pytest.raises(crud.NotFoundError):
            crud.get_board_by_key(session, 2, "mine")
        column = crud.create_column(session, board.id)
        assert column.id is not None
        (card,) = _cards(session, column.id, "x")
        assert card.id is not None
        with pytest.raises(crud.NotFoundError):
            crud.get_column(session, 2, column.id)
        with pytest.raises(crud.NotFoundError):
            crud.get_card(session, 2, card.id)
        with pytest.raises(crud.NotFoundError):
            crud.check_cards_owned(session, 2, [card.id])
        crud.check_cards_owned(session, 1, [card.id])

    def test_delete_cascades(self, session):
        board = _board(session)
        assert board.id is not None
        column = crud.create_column(session, board.id)
        assert column.id is not None
        _cards(session, column.id, "a")
        crud.delete_board(session, board)
        assert session.get(Card, 1) is None


class TestColumn:
    def test_unique_default_name_and_rename(self, session):
        board = _board(session)
        assert board.id is not None
        c1 = crud.create_column(session, board.id)
        c2 = crud.create_column(session, board.id)
        assert (c1.name, c2.name, c2.position) == ("New Column", "New Column 2", 1)
        with pytest.raises(crud.ConflictError, match="already exists"):
            crud.update_column_name(session, c2, " New Column ")
        crud.update_column_name(session, c2, " Done ")
        assert c2.name == "Done"

    def test_order(self, session):
        board = _board(session)
        assert board.id is not None
        ids = [crud.create_column(session, board.id).id for _ in range(3)]
        crud.update_column_order(session, board, [ids[2], ids[0], ids[1]])  # type: ignore[list-item]
        assert [c.id for c in crud._get_columns(session, board.id)] == [  # noqa: SLF001
            ids[2],
            ids[0],
            ids[1],
        ]
        with pytest.raises(crud.NotFoundError):
            crud.update_column_order(session, board, [ids[0]])  # type: ignore[list-item]


class TestCard:
    @pytest.fixture
    def cols(self, session) -> tuple[int, int]:
        board = _board(session)
        assert board.id is not None
        a = crud.create_column(session, board.id).id
        b = crud.create_column(session, board.id).id
        assert a is not None
        assert b is not None
        return a, b

    def test_create_cleans_title(self, session, cols):
        (card,) = _cards(session, cols[0], "  a \t  b \r\nc  ")
        assert card.title == "a b \nc"

    def test_update(self, session, cols):
        (card,) = _cards(session, cols[0], "x")
        crud.update_card(
            session, card, {"is_completed": True, "prio": True, "is_revive": True}
        )
        assert card.is_completed
        assert card.prio is True
        assert card.is_revive
        crud.update_card(session, card, {"is_completed": False, "prio": None})
        assert not card.is_completed
        assert card.prio is None
        crud.update_card(session, card, {"title": "   "})
        assert card.title == "x"

    def test_move_renumbers(self, session, cols):
        a, b = cols
        c1, _c2, _c3 = _cards(session, a, "1", "2", "3")
        _cards(session, b, "x", "y")
        crud.move_card(session, c1, b, 1)
        assert _titles(session, a) == ["2", "3"]
        assert _titles(session, b) == ["x", "1", "y"]
        assert [c.position for c in crud._get_cards(session, b)] == [0, 1, 2]  # noqa: SLF001
        crud.move_card(session, c1, b, None)
        assert _titles(session, b) == ["x", "y", "1"]
        crud.move_card(session, c1, b, 0)
        assert _titles(session, b) == ["1", "x", "y"]

    def test_copy(self, session, cols):
        a, b = cols
        (card,) = _cards(session, a, "x")
        crud.update_card(session, card, {"is_completed": True, "prio": False})
        new = crud.copy_card(session, card, b)
        assert (new.title, new.prio, new.is_completed) == ("x", False, False)

    def test_bulk(self, session, cols):
        label = crud.save_label(session, Label(), "L", "#123456")
        cards = _cards(session, cols[0], "1", "2")
        ids = [c.id for c in cards if c.id is not None]
        crud.bulk_update_cards(
            session,
            ids,
            {"label_id": label.id, "prio": True, "is_revive": True},
        )
        for c in cards:
            session.refresh(c)
        assert all(c.label_id == label.id and c.prio and c.is_revive for c in cards)
        crud.bulk_update_cards(session, ids, {"label_id": None})
        for c in cards:
            session.refresh(c)
        assert all(c.label_id is None and c.prio for c in cards)
        # is_revive is not nullable: explicit null must not touch it
        crud.bulk_update_cards(session, ids, {"is_revive": None, "prio": None})
        for c in cards:
            session.refresh(c)
        assert all(c.is_revive and c.prio is None for c in cards)

    def test_delete_on_board_without_columns(self, session):
        board = _board(session, "empty")
        assert board.id is not None
        assert crud.delete_cards(session, board.id, "all") == 0

    @pytest.mark.parametrize(
        ("mode", "remaining", "repeat_reset"),
        [
            ("completed", ["open", "repeat"], True),
            ("all", ["repeat"], True),
            ("2w", ["open", "recent", "repeat"], False),
        ],
    )
    def test_delete_modes(self, session, cols, mode, remaining, repeat_reset):
        a = cols[0]
        board_id = crud.get_column(session, 1, a).board_id
        _open, old, recent, repeat = _cards(
            session, a, "open", "old", "recent", "repeat"
        )
        for c in (old, recent, repeat):
            crud.update_card(session, c, {"is_completed": True})
        old.date_completed = utcnow() - timedelta(days=30)
        repeat.date_completed = utcnow() - timedelta(days=30)
        repeat.is_revive = True
        session.add_all([old, repeat])
        session.commit()
        preview = {c.title for c in crud.get_deletable_cards(session, board_id, mode)}
        count = crud.delete_cards(session, board_id, mode)
        assert count == len(preview)
        assert sorted(_titles(session, a)) == remaining
        session.refresh(repeat)
        assert (repeat.date_completed is None) is repeat_reset

    def test_sort(self, session, cols):
        a = cols[0]
        board = crud.get_board(session, 1, crud.get_column(session, 1, a).board_id)
        lbl = crud.save_label(session, Label(), "Alpha", "#000000")
        done, _plain, labeled, prio = _cards(session, a, "done", "b", "a", "prio")
        crud.update_card(session, done, {"is_completed": True, "prio": True})
        crud.update_card(session, labeled, {"label_id": lbl.id})
        crud.update_card(session, prio, {"prio": True})
        crud.sort_cards(session, board, "prio")
        session.expire_all()
        assert _titles(session, a) == ["prio", "b", "a", "done"]
        crud.sort_cards(session, board, "date")
        session.expire_all()
        assert _titles(session, a) == ["b", "a", "prio", "done"]


class TestLabel:
    def test_validation(self, session):
        lbl = crud.save_label(session, Label(), " Work ", " #FF0000 ")
        assert (lbl.name, lbl.color) == ("Work", "#ff0000")
        crud.save_label(session, lbl, "Work", "#ff0000")  # own values ok
        with pytest.raises(crud.ConflictError, match="Invalid color"):
            crud.save_label(session, Label(), "X", "red")
        with pytest.raises(crud.ConflictError, match="name 'Work' already"):
            crud.save_label(session, Label(), "Work", "#00ff00")
        with pytest.raises(crud.ConflictError, match="already in use"):
            crud.save_label(session, Label(), "Home", "#ff0000")

    def test_delete_clears_cards(self, session):
        board = _board(session)
        assert board.id is not None
        column = crud.create_column(session, board.id)
        assert column.id is not None
        (card,) = _cards(session, column.id, "x")
        lbl = crud.save_label(session, Label(), "L", "#111111")
        crud.update_card(session, card, {"label_id": lbl.id})
        crud.delete_label(session, lbl)
        session.expire_all()
        assert crud.get_card(session, 1, card.id).label_id is None  # type: ignore[arg-type]


class TestUserAndMigration:
    def test_secret_lookup(self, session):
        user = crud.get_user_by_secret(session, "test", verify_secret)
        assert user is not None
        assert user.id == 1
        assert crud.get_user_by_secret(session, "other", verify_secret).id == 2  # type: ignore[union-attr]
        assert crud.get_user_by_secret(session, "nope", verify_secret) is None

    def test_hash_secret_roundtrip(self):
        hashed = hash_secret("s3cret")
        assert hashed != "s3cret"
        assert verify_secret("s3cret", hashed)
        assert not verify_secret("wrong", hashed)


class TestMember:
    def test_member_access(self, session):
        board = _board(session, "shared", owner_id=1)
        assert board.id is not None
        column = crud.create_column(session, board.id)
        assert column.id is not None
        (card,) = _cards(session, column.id, "x")
        assert card.id is not None
        crud.add_board_member(session, board, 2)
        crud.add_board_member(session, board, 2)  # idempotent
        assert crud.get_board_by_key(session, 2, "shared").id == board.id
        assert [b.id for b in crud.get_boards_with_columns(session, 2)] == [board.id]
        crud.get_card(session, 2, card.id)
        crud.check_cards_owned(session, 2, [card.id])
        crud.get_column(session, 2, column.id, owner_only=False)
        # board/column management stays owner-only
        with pytest.raises(crud.NotFoundError):
            crud.get_board(session, 2, board.id)
        with pytest.raises(crud.NotFoundError):
            crud.get_column(session, 2, column.id)

    def test_owner_also_member(self, session):
        board = _board(session, "mine", owner_id=1)
        assert board.id is not None
        crud.add_board_member(session, board, 1)
        assert len(crud.get_boards_with_columns(session, 1)) == 1
        crud.get_board(session, 1, board.id)
        crud.get_board_by_key(session, 1, "mine")

    def test_delete_board_removes_members(self, session):
        board = _board(session, "gone", owner_id=1)
        crud.add_board_member(session, board, 2)
        crud.delete_board(session, board)
        assert session.exec(select(BoardMember)).all() == []

    def test_user_name_unique_case_insensitive(self, session):
        assert crud.get_user_by_name(session, " other ").id == 2  # type: ignore[union-attr]
        session.add(User(id=3, name="OTHER"))
        with pytest.raises(IntegrityError):
            session.commit()
