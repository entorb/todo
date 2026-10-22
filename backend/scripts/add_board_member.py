#!/usr/bin/env python3.11
"""
Give a user card access to a board (no board/column management).

./scripts/add_board_member.py <board.key|id> <user.name|id>
or: python3.11 -m scripts.add_board_member <board.key|id> <user.name|id>

All-digit arguments are treated as ids.
"""

import sys
from pathlib import Path

# run directly: make `app` importable (backend/ is not on sys.path then)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import crud
from app.core.db import get_engine
from app.models import Board, User
from sqlmodel import Session, select


def main() -> None:
    """Add user (name or id) as member of board (key or id)."""
    if len(sys.argv) != 3:  # noqa: PLR2004
        print(__doc__)
        sys.exit(1)
    board_arg, user_arg = sys.argv[1].strip(), sys.argv[2].strip()
    crud.init_db()
    with Session(get_engine()) as s:
        board = (
            s.get(Board, int(board_arg))
            if board_arg.isdigit()
            else s.exec(select(Board).where(Board.key == board_arg.lower())).first()
        )
        user = (
            s.get(User, int(user_arg))
            if user_arg.isdigit()
            else crud.get_user_by_name(s, user_arg)
        )
        if board is None or user is None:
            print("Error: board or user not found")
            sys.exit(1)
        crud.add_board_member(s, board, user.id)  # type: ignore[arg-type]
        print(f"User '{user.name}' added to board '{board.key}'")


if __name__ == "__main__":
    main()
