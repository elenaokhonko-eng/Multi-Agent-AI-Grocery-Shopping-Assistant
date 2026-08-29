from uuid import UUID

from domain.models.core import StoreQuote
from sqlmodel import Session, select


class QuoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_run_quotes(self, run_id: UUID) -> list[StoreQuote]:
        return list(self.session.exec(
            select(StoreQuote).where(StoreQuote.run_id == run_id)
        ).all())
