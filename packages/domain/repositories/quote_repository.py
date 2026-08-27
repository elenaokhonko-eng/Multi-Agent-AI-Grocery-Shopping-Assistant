from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select
from domain.models.core import StoreQuote, ComparisonRun, QuoteLine


class QuoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(self, shopping_list_id: UUID) -> ComparisonRun:
        run = ComparisonRun(shopping_list_id=shopping_list_id)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def create_quote(
        self, 
        run_id: UUID, 
        store_name: str, 
        subtotal_cents: int, 
        delivery_fee_cents: int, 
        is_complete: bool
    ) -> StoreQuote:
        quote = StoreQuote(
            run_id=run_id,
            store_name=store_name,
            subtotal_cents=subtotal_cents,
            delivery_fee_cents=delivery_fee_cents,
            total_cents=subtotal_cents + delivery_fee_cents,
            is_complete=is_complete
        )
        self.session.add(quote)
        self.session.commit()
        self.session.refresh(quote)
        return quote

    def add_line_item(
        self, 
        quote_id: UUID, 
        candidate_id: UUID, 
        quantity: int, 
        line_total_cents: int
    ) -> QuoteLine:
        line = QuoteLine(
            quote_id=quote_id,
            candidate_id=candidate_id,
            quantity=quantity,
            line_total_cents=line_total_cents
        )
        self.session.add(line)
        self.session.commit()
        self.session.refresh(line)
        return line

    def get_run_quotes(self, run_id: UUID) -> List[StoreQuote]:
        return self.session.exec(
            select(StoreQuote).where(StoreQuote.run_id == run_id)
        ).all()
