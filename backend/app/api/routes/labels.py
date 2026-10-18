"""Label endpoints. Labels are global, shared by all boards."""

from fastapi import APIRouter, Response, status

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Label, LabelIn, LabelPublic

router = APIRouter()


@router.get("")
def list_labels(session: SessionDep, _: CurrentUser) -> list[LabelPublic]:
    """List all labels, ordered by name."""
    return [
        LabelPublic.model_validate(lb, from_attributes=True)
        for lb in crud.get_labels(session)
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_label(data: LabelIn, session: SessionDep, _: CurrentUser) -> LabelPublic:
    """Create a label, name and color must be unique."""
    label = crud.save_label(session, Label(), data.name, data.color)
    return LabelPublic.model_validate(label, from_attributes=True)


@router.patch("/{label_id}")
def update_label(
    label_id: int, data: LabelIn, session: SessionDep, _: CurrentUser
) -> LabelPublic:
    """Update label name and color."""
    label = crud.save_label(
        session, crud.get_label(session, label_id), data.name, data.color
    )
    return LabelPublic.model_validate(label, from_attributes=True)


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(label_id: int, session: SessionDep, _: CurrentUser) -> Response:
    """Delete a label, cards lose it."""
    crud.delete_label(session, crud.get_label(session, label_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
