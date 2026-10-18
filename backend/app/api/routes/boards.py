"""Board endpoints."""

from typing import Literal

from fastapi import APIRouter, Response, status

from app import crud, export_service
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Board,
    BoardCreate,
    BoardPublic,
    BoardSummary,
    BoardUpdate,
    CardPublic,
    CountResponse,
    ExportResponse,
    IdList,
)

router = APIRouter()

DeleteMode = Literal["completed", "all", "2w"]


@router.get("")
def list_boards(session: SessionDep, user: CurrentUser) -> list[BoardSummary]:
    """List own boards incl. column names."""
    boards = crud.get_boards_with_columns(session, user.user_id)
    return [BoardSummary.model_validate(b, from_attributes=True) for b in boards]


@router.get("/{key}")
def get_board(
    key: str, session: SessionDep, user: CurrentUser, *, touch: bool = False
) -> BoardPublic:
    """Get board by key incl. columns and cards. touch=true updates last_login."""
    board = crud.get_board_by_key(session, user.user_id, key)
    if touch:
        crud.touch_last_login(session, board)
    return _public(board)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_board(
    data: BoardCreate, session: SessionDep, user: CurrentUser
) -> BoardSummary:
    """Create a board, key defaults to lowercased name."""
    board = crud.add_board(session, user.user_id, data.key or data.name, data.name)
    return BoardSummary.model_validate(board, from_attributes=True)


@router.patch("/{board_id}")
def update_board(
    board_id: int, data: BoardUpdate, session: SessionDep, user: CurrentUser
) -> BoardSummary:
    """Rename board and/or change its key."""
    board = crud.get_board(session, user.user_id, board_id)
    board = crud.update_board(session, board, data.name, data.key)
    return BoardSummary.model_validate(board, from_attributes=True)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, session: SessionDep, user: CurrentUser) -> Response:
    """Delete board incl. columns and cards."""
    crud.delete_board(session, crud.get_board(session, user.user_id, board_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{board_id}/columns/order", status_code=status.HTTP_204_NO_CONTENT)
def reorder_columns(
    board_id: int, data: IdList, session: SessionDep, user: CurrentUser
) -> Response:
    """Set column order."""
    board = crud.get_board(session, user.user_id, board_id)
    crud.update_column_order(session, board, data.ids)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{board_id}/sort", status_code=status.HTTP_204_NO_CONTENT)
def sort_board(
    board_id: int,
    by: Literal["prio", "date"],
    session: SessionDep,
    user: CurrentUser,
) -> Response:
    """Sort cards of all columns by prio/label/title or by date."""
    crud.sort_cards(session, crud.get_board(session, user.user_id, board_id), by)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{board_id}/export")
def export_board(
    board_id: int,
    session: SessionDep,
    user: CurrentUser,
    fmt: Literal["txt", "markdown", "html"] = "txt",
    *,
    completed_only: bool = True,
) -> ExportResponse:
    """Export cards as txt, markdown or html."""
    board = crud.get_board(session, user.user_id, board_id)
    text = export_service.export(
        board, crud.get_labels(session), completed_only=completed_only, fmt=fmt
    )
    return ExportResponse(text=text)


@router.get("/{board_id}/cards/deletable")
def deletable_cards(
    board_id: int, mode: DeleteMode, session: SessionDep, user: CurrentUser
) -> list[CardPublic]:
    """Preview of cards a delete with this mode would remove."""
    crud.get_board(session, user.user_id, board_id)
    cards = crud.get_deletable_cards(session, board_id, mode)
    return [CardPublic.model_validate(c, from_attributes=True) for c in cards]


@router.delete("/{board_id}/cards")
def delete_cards(
    board_id: int, mode: DeleteMode, session: SessionDep, user: CurrentUser
) -> CountResponse:
    """Delete non-repeat cards (completed, all, completed > 2 weeks)."""
    crud.get_board(session, user.user_id, board_id)
    return CountResponse(count=crud.delete_cards(session, board_id, mode))


def _public(board: Board) -> BoardPublic:
    return BoardPublic.model_validate(board, from_attributes=True)
