"""Login endpoint."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app import crud
from app.api.deps import SessionDep, limiter
from app.core.security import create_access_token, verify_secret
from app.models import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,  # noqa: ARG001 required by slowapi
    login_request: LoginRequest,
    session: SessionDep,
) -> TokenResponse:
    """Authenticate by secret and return a JWT."""
    user = crud.get_user_by_secret(session, login_request.secret, verify_secret)
    if user is None or user.id is None:
        logger.warning("Failed login attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    logger.info("Login of user %s", user.name[0:3])
    return TokenResponse(access_token=create_access_token(user.id, user.name))
