from uuid import UUID

from domain.models.core import ShoppingList, ShoppingListItem
from sqlmodel import Session, select


class ShoppingListRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str) -> ShoppingList:
        sl = ShoppingList(name=name)
        self.session.add(sl)
        self.session.commit()
        self.session.refresh(sl)
        return sl

    def get_by_id(self, shopping_list_id: UUID) -> ShoppingList | None:
        return self.session.get(ShoppingList, shopping_list_id)

    def list_all(self) -> list[ShoppingList]:
        return list(self.session.exec(select(ShoppingList)).all())

    def add_item(
        self, shopping_list_id: UUID, name: str, quantity: int = 1, must_have: bool = True
    ) -> ShoppingListItem:
        item = ShoppingListItem(
            shopping_list_id=shopping_list_id,
            name=name,
            desired_quantity=quantity,
            must_have=must_have,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
