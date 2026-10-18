"""Column endpoints."""

from fastapi import APIRouter, Response, status

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import ColumnCreate, ColumnPublic, ColumnUpdate

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_column(
    data: ColumnCreate, session: SessionDep, user: CurrentUser
) -> ColumnPublic:
    """Create a column with unique default name at the end of the board."""
    crud.get_board(session, user.user_id, data.board_id)
    column = crud.create_column(session, data.board_id)
    return ColumnPublic.model_validate(column, from_attributes=True)


@router.patch("/{column_id}")
def update_column(
    column_id: int, data: ColumnUpdate, session: SessionDep, user: CurrentUser
) -> ColumnPublic:
    """Rename a column."""
    column = crud.get_column(session, user.user_id, column_id)
    column = crud.update_column_name(session, column, data.name)
    return ColumnPublic.model_validate(column, from_attributes=True)


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(column_id: int, session: SessionDep, user: CurrentUser) -> Response:
    """Delete a column incl. its cards."""
    crud.delete_column(session, crud.get_column(session, user.user_id, column_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
