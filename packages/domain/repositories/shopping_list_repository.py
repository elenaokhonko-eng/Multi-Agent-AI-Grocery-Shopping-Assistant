from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select
from domain.models.core import ShoppingList, ShoppingListItem


class ShoppingListRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str) -> ShoppingList:
        sl = ShoppingList(name=name)
        self.session.add(sl)
        self.session.commit()
        self.session.refresh(sl)
        return sl

    def get_by_id(self, shopping_list_id: UUID) -> Optional[ShoppingList]:
        return self.session.get(ShoppingList, shopping_list_id)

    def list_all(self) -> List[ShoppingList]:
        return self.session.exec(select(ShoppingList)).all()

    def add_item(self, shopping_list_id: UUID, keyword: str, quantity: int, must_have: bool = False) -> ShoppingListItem:
        item = ShoppingListItem(
            shopping_list_id=shopping_list_id,
            keyword=keyword,
            quantity=quantity,
            must_have=must_have
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
