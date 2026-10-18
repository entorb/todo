"""
Set or create a user's login secret.

uv run python -m scripts.set_user_secret <user_id> [<name>]
"""

import getpass
import sys

from app import crud
from app.core.db import get_engine
from app.core.security import hash_secret
from app.models import User
from sqlmodel import Session


def main() -> None:
    """Prompt for secret, store bcrypt hash."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print(__doc__)
        sys.exit(1)
    user_id = int(sys.argv[1])
    crud.init_db()
    with Session(get_engine()) as s:
        user = s.get(User, user_id)
        if user is None:
            if len(sys.argv) < 3:  # noqa: PLR2004
                print(f"User {user_id} missing, pass a name to create it.")
                sys.exit(1)
            user = User(id=user_id, name=sys.argv[2])
        secret = getpass.getpass("Secret: ")
        if len(secret) < 12:  # noqa: PLR2004
            print("Secret must have at least 12 characters.")
            sys.exit(1)
        if getpass.getpass("Repeat: ") != secret:
            print("Secrets differ.")
            sys.exit(1)
        user.secret_hashed = hash_secret(secret)
        s.add(user)
        s.commit()
        print(f"Secret set for user {user.id} ({user.name}).")


if __name__ == "__main__":
    main()
