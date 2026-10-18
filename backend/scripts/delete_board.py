"""
Delete a board by key or id.

uv run python -m scripts.delete_board <key_or_id>
"""

import sys

from app import crud
from app.core.db import get_engine
from app.models import Board
from sqlmodel import Session, select


def main() -> None:
    """Delete board incl. columns and cards."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print(__doc__)
        sys.exit(1)
    arg = sys.argv[1]
    with Session(get_engine()) as s:
        board = s.exec(select(Board).where(Board.key == arg)).first()
        if board is None and arg.isdigit():
            board = s.get(Board, int(arg))
        if board is None:
            print(f"Error: board '{arg}' not found")
            sys.exit(1)
        board_id, key = board.id, board.key
        crud.delete_board(s, board)
        print(f"Board {board_id} ('{key}') deleted successfully.")


if __name__ == "__main__":
    main()
