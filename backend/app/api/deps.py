"""FastAPI dependencies: DB session, current user, rate limiter."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import get_session
from app.core.security import decode_token
from app.models import UserInfo

SessionDep = Annotated[Session, Depends(get_session)]

# client IP from X-Forwarded-For, requires uvicorn/gunicorn proxy headers
limiter = Limiter(key_func=get_remote_address, enabled=get_settings().env == "PROD")

security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserInfo:
    """Validate the Bearer JWT and return the user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc
    user_id = payload.get("user_id")
    username = payload.get("username")
    if not isinstance(user_id, int) or not isinstance(username, str):
        raise credentials_exception
    return UserInfo(user_id=user_id, user_name=username)


CurrentUser = Annotated[UserInfo, Depends(get_current_user)]
