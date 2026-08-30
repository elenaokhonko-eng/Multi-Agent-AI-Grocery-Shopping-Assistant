from datetime import UTC, datetime
from uuid import UUID

from domain.models.core import ShoppingList, ShoppingListItem
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from apps.api.core import get_session
from apps.api.schemas import (
    ShoppingListCreate,
    ShoppingListItemCreate,
    ShoppingListItemUpdate,
    ShoppingListRead,
)

router = APIRouter(prefix="/shopping-lists", tags=["Shopping Lists"])


@router.get("", response_model=list[ShoppingListRead])
def list_shopping_lists(session: Session = Depends(get_session)):
    lists = session.exec(select(ShoppingList).where(ShoppingList.is_active == True)).all()  # noqa: E712
    return lists


@router.post("", response_model=ShoppingListRead, status_code=status.HTTP_201_CREATED)
def create_shopping_list(list_data: ShoppingListCreate, session: Session = Depends(get_session)):
    new_list = ShoppingList(
        name=list_data.name,
        description=list_data.description,
        version=1,
        is_active=True,
    )
    session.add(new_list)
    session.commit()
    session.refresh(new_list)

    for item_data in list_data.items:
        item = ShoppingListItem(
            shopping_list_id=new_list.id,
            name=item_data.name,
            category=item_data.category,
            desired_quantity=item_data.desired_quantity,
            unit_measure=item_data.unit_measure,
            min_pack_size=item_data.min_pack_size,
            max_pack_size=item_data.max_pack_size,
            must_have=item_data.must_have,
            is_enabled=item_data.is_enabled,
            substitution_policy=item_data.substitution_policy,
            preferred_brands=item_data.preferred_brands,
            exclusions=item_data.exclusions,
            pinned_skus=item_data.pinned_skus,
        )
        session.add(item)
    session.commit()
    session.refresh(new_list)
    return new_list


@router.get("/{list_id}", response_model=ShoppingListRead)
def get_shopping_list(list_id: UUID, session: Session = Depends(get_session)):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")
    return sl


@router.put("/{list_id}", response_model=ShoppingListRead)
def update_shopping_list(list_id: UUID, list_data: ShoppingListCreate, session: Session = Depends(get_session)):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    sl.name = list_data.name
    sl.description = list_data.description
    sl.version += 1
    sl.updated_at = datetime.now(UTC)
    session.add(sl)
    session.commit()
    session.refresh(sl)
    return sl


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_list(list_id: UUID, session: Session = Depends(get_session)):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    sl.is_active = False
    sl.updated_at = datetime.now(UTC)
    session.add(sl)
    session.commit()


@router.post("/{list_id}/items", response_model=ShoppingListItem, status_code=status.HTTP_201_CREATED)
def add_item_to_shopping_list(
    list_id: UUID,
    item_data: ShoppingListItemCreate,
    session: Session = Depends(get_session),
):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    item = ShoppingListItem(
        shopping_list_id=sl.id,
        name=item_data.name,
        category=item_data.category,
        desired_quantity=item_data.desired_quantity,
        unit_measure=item_data.unit_measure,
        min_pack_size=item_data.min_pack_size,
        max_pack_size=item_data.max_pack_size,
        must_have=item_data.must_have,
        is_enabled=item_data.is_enabled,
        substitution_policy=item_data.substitution_policy,
        preferred_brands=item_data.preferred_brands,
        exclusions=item_data.exclusions,
        pinned_skus=item_data.pinned_skus,
    )
    session.add(item)
    sl.version += 1
    sl.updated_at = datetime.now(UTC)
    session.add(sl)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{list_id}/items/{item_id}", response_model=ShoppingListItem)
@router.patch("/{list_id}/items/{item_id}", response_model=ShoppingListItem)
def update_shopping_list_item(
    list_id: UUID,
    item_id: UUID,
    item_data: ShoppingListItemUpdate,
    session: Session = Depends(get_session),
):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found on this shopping list")

    update_dict = item_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(item, k, v)

    item.updated_at = datetime.now(UTC)
    session.add(item)
    sl.version += 1
    sl.updated_at = datetime.now(UTC)
    session.add(sl)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_list_item(
    list_id: UUID,
    item_id: UUID,
    session: Session = Depends(get_session),
):
    sl = session.get(ShoppingList, list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found on this shopping list")

    session.delete(item)
    sl.version += 1
    sl.updated_at = datetime.now(UTC)
    session.add(sl)
    session.commit()
