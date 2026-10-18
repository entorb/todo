"""Card endpoints."""

from fastapi import APIRouter, Response, status

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import CardBulkUpdate, CardCreate, CardMove, CardPublic, CardUpdate

router = APIRouter()


def _check_label(session: SessionDep, data: dict) -> None:
    if data.get("label_id") is not None:
        crud.get_label(session, data["label_id"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_card(data: CardCreate, session: SessionDep, user: CurrentUser) -> CardPublic:
    """Create a card at the end of a column."""
    crud.get_column(session, user.user_id, data.column_id)
    card = crud.create_card(session, data.column_id, data.title)
    return CardPublic.model_validate(card, from_attributes=True)


# before /{card_id}, else "bulk" is parsed as id
@router.patch("/bulk", status_code=status.HTTP_204_NO_CONTENT)
def bulk_update_cards(
    data: CardBulkUpdate, session: SessionDep, user: CurrentUser
) -> Response:
    """Set repeat / prio / label on many cards. Explicit null unsets prio/label."""
    crud.check_cards_owned(session, user.user_id, data.ids)
    values = data.model_dump(exclude_unset=True, exclude={"ids"})
    _check_label(session, values)
    crud.bulk_update_cards(session, data.ids, values)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{card_id}")
def update_card(
    card_id: int, data: CardUpdate, session: SessionDep, user: CurrentUser
) -> CardPublic:
    """Partial update. Explicit null unsets prio/label."""
    card = crud.get_card(session, user.user_id, card_id)
    values = data.model_dump(exclude_unset=True)
    _check_label(session, values)
    card = crud.update_card(session, card, values)
    return CardPublic.model_validate(card, from_attributes=True)


@router.post("/{card_id}/move")
def move_card(
    card_id: int, data: CardMove, session: SessionDep, user: CurrentUser
) -> CardPublic:
    """Move a card to column/position (default: end)."""
    card = crud.get_card(session, user.user_id, card_id)
    crud.get_column(session, user.user_id, data.column_id)
    card = crud.move_card(session, card, data.column_id, data.position)
    return CardPublic.model_validate(card, from_attributes=True)


@router.post("/{card_id}/copy", status_code=status.HTTP_201_CREATED)
def copy_card(
    card_id: int, data: CardMove, session: SessionDep, user: CurrentUser
) -> CardPublic:
    """Copy a card to the end of a column."""
    card = crud.get_card(session, user.user_id, card_id)
    crud.get_column(session, user.user_id, data.column_id)
    new_card = crud.copy_card(session, card, data.column_id)
    return CardPublic.model_validate(new_card, from_attributes=True)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, session: SessionDep, user: CurrentUser) -> Response:
    """Delete a card."""
    crud.delete_card(session, crud.get_card(session, user.user_id, card_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
