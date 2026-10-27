"""FastAPI application."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import crud
from app.api.deps import limiter
from app.api.routes import auth, boards, cards, columns, labels
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
settings = get_settings()

if settings.env == "PROD":
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn="https://7ca6442c26bbc22d5f6ce361630dd03e@o4507139041525760.ingest.de.sentry.io/4512292047552592",
        integrations=[
            LoggingIntegration(capture_sentry_logs=True),
        ],
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Create tables and run migrations on startup."""
    crud.init_db()
    yield


app = FastAPI(
    title="Todo API",
    description="Kanban todo boards",
    version="0.1.0",
    # same root for prod and dev to make debugging easier
    root_path="/be/todo",
    lifespan=lifespan,
    # clean operation ids -> clean names in generated TS client
    generate_unique_id_function=lambda route: route.name,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


@app.exception_handler(crud.NotFoundError)
async def _not_found(_request: Request, _exc: crud.NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"}
    )


@app.exception_handler(crud.ConflictError)
async def _conflict(_request: Request, exc: crud.ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


# Bearer token auth, no cookies -> no allow_credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(boards.router, prefix="/api/boards", tags=["boards"])
app.include_router(columns.router, prefix="/api/columns", tags=["columns"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(labels.router, prefix="/api/labels", tags=["labels"])


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.env}


# https://entorb.net/be/todo/sentry-test
@app.get("/sentry-test")
async def trigger_error() -> None:
    """Test."""
    _ = 1 / 0
