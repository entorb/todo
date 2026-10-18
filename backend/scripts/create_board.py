"""
Create a board.

uv run python -m scripts.create_board <name> [<user_id>]
"""

import sys

from app import crud
from app.core.db import get_engine
from sqlmodel import Session


def main() -> None:
    """Create board with key = lowercased name."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1]
    owner_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1  # noqa: PLR2004
    crud.init_db()
    with Session(get_engine()) as s:
        try:
            board = crud.add_board(s, owner_id, name, name)
        except crud.ConflictError as e:
            print(f"Error: {e}")
            sys.exit(1)
        print(f"Board created: name='{board.name}' key='{board.key}'")


if __name__ == "__main__":
    main()
