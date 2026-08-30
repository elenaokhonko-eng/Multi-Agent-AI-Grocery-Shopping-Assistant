import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from apps.browser_worker.session_manager import SessionManager
from packages.domain.services.matching import is_excluded_by_negative_filter
from packages.retailers.base import (
    AuthoritativeCart,
    CandidateProduct,
    CartDiff,
    CartLine,
    DeliverySlot,
    OrderConfirmation,
    RetailerAdapter,
    SessionStatus,
)
from packages.retailers.fairprice.page_objects import FairPricePageObject


class FairPriceAdapter(RetailerAdapter):
    retailer_id = "fairprice"

    def __init__(self, session_profile_dir: str | None = None):
        sm = SessionManager()
        self.session_profile_dir = session_profile_dir or str(sm.get_profile_path(self.retailer_id))
        self._cart_lines: dict[str, CartLine] = {}
        self._selected_slot: DeliverySlot | None = None
        self._page_object = FairPricePageObject()

    async def check_session(self) -> SessionStatus:
        return await self._page_object.check_session_status(self.session_profile_dir)

    async def resolve_pinned_sku(self, sku: str) -> CandidateProduct | None:
        if not sku or not sku.startswith("FP_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"FairPrice Pinned Item {sku}",
            brand="FairPrice",
            category="Groceries",
            price_cents=635,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=318,
            product_url=f"https://www.fairprice.com.sg/product/{sku}",
            image_url=f"https://images.fairprice.com.sg/{sku}.jpg",
            in_stock=True,
            is_exact_match=True,
        )

    async def search_candidates(self, query: str, category_hint: str | None = None) -> list[CandidateProduct]:
        clean_query = query.lower().strip()
        candidates: list[CandidateProduct] = []

        # 1. Live Online Search via FairPricePageObject
        live_items = await self._page_object.search_products(clean_query)
        for item in live_items:
            is_excluded, _exc_reason = is_excluded_by_negative_filter(item.title, category=item.category)
            if is_excluded:
                continue
            candidates.append(item)

        # 2. MOCK_FIXTURE — for offline/test use only.
        # In live runs (ALLOW_MOCK_FALLBACK != true) a search miss is a hard failure.
        if not candidates:
            if os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() != "true":
                raise RuntimeError(
                    f"LIVE_RUN_MOCK_BLOCKED: FairPrice live search returned no results for '{query}'. "
                    "Set ALLOW_MOCK_FALLBACK=true only in test environments."
                )
            catalog = [
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="FP_102030",
                    title="Meiji Fresh Milk 2L",
                    brand="Meiji",
                    category="Dairy & Chilled",
                    price_cents=635,
                    pack_size="2L",
                    unit_measure="L",
                    unit_price_cents=318,
                    product_url="https://www.fairprice.com.sg/product/meiji-fresh-milk-2l-102030",
                    image_url="https://images.fairprice.com.sg/102030.jpg",
                    in_stock=True,
                    is_exact_match=False,  # Mock fixture — not a verified live match
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="FP_112233",
                    title="Dasoon Fresh Eggs 10s (600g)",
                    brand="Dasoon",
                    category="Eggs",
                    price_cents=345,
                    pack_size="10s",
                    unit_measure="pack",
                    unit_price_cents=345,
                    product_url="https://www.fairprice.com.sg/product/dasoon-fresh-eggs-112233",
                    image_url="https://images.fairprice.com.sg/112233.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="FP_123456",
                    title="Fresh Lemons 3s Pack",
                    brand="FairPrice Fresh",
                    category="Fresh Produce",
                    price_cents=250,
                    pack_size="3s",
                    unit_measure="pack",
                    unit_price_cents=83,
                    product_url="https://www.fairprice.com.sg/product/fresh-lemons-123456",
                    image_url="https://images.fairprice.com.sg/123456.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="FP_133445",
                    title="San Pellegrino Sparkling Water 1L",
                    brand="San Pellegrino",
                    category="Beverages",
                    price_cents=320,
                    pack_size="1L",
                    unit_measure="L",
                    unit_price_cents=320,
                    product_url="https://www.fairprice.com.sg/product/san-pellegrino-1l-133445",
                    image_url="https://images.fairprice.com.sg/133445.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
            ]
            for p in catalog:
                if any(w in p.title.lower() for w in clean_query.split()):
                    is_excluded, _ = is_excluded_by_negative_filter(p.title, category=p.category)
                    if not is_excluded:
                        candidates.append(p)

        return candidates

    async def add_item_to_cart(self, sku: str, quantity: int) -> bool:
        if quantity <= 0:
            return False
        unit_price = 345
        title = f"FairPrice Item {sku}"
        if "102030" in sku or "milk" in sku.lower():
            unit_price = 635
            title = "Meiji Fresh Milk 2L"
        elif "123456" in sku or "lemon" in sku.lower():
            unit_price = 250
            title = "Fresh Lemons 3s Pack"
        elif "133445" in sku or "water" in sku.lower():
            unit_price = 320
            title = "San Pellegrino Sparkling Water 1L"

        self._cart_lines[sku] = CartLine(
            retailer_sku=sku,
            title=title,
            quantity=quantity,
            unit_price_cents=unit_price,
            line_total_cents=unit_price * quantity,
            is_unowned=False,
        )
        return True

    async def read_cart(self) -> AuthoritativeCart:
        subtotal = sum(line.line_total_cents for line in self._cart_lines.values())
        threshold = 8000  # $80.00 free delivery threshold
        delivery_fee = 0 if subtotal >= threshold else 599
        service_fee = 199
        bag_fee = 20
        slot_fee = self._selected_slot.fee_cents if self._selected_slot else 0
        gross = subtotal + delivery_fee + service_fee + bag_fee + slot_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_fp_{uuid4().hex[:8]}",
            cart_url="https://www.fairprice.com.sg/cart",
            lines=list(self._cart_lines.values()),
            subtotal_cents=subtotal,
            delivery_fee_cents=delivery_fee,
            service_fee_cents=service_fee,
            bag_fee_cents=bag_fee,
            slot_fee_cents=slot_fee,
            gross_total_cents=gross,
            free_delivery_threshold_cents=threshold,
            unowned_items_detected=False,
        )

    async def list_delivery_slots(self) -> list[DeliverySlot]:
        now = datetime.now(UTC)
        return [
            DeliverySlot(
                slot_id="slot_fp_morning",
                start_time=now + timedelta(hours=14),
                end_time=now + timedelta(hours=16),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 08:00 - 10:00 AM (Standard)",
            ),
            DeliverySlot(
                slot_id="slot_fp_evening",
                start_time=now + timedelta(hours=22),
                end_time=now + timedelta(hours=24),
                fee_cents=200,
                is_available=True,
                display_label="Tomorrow 06:00 - 08:00 PM (Peak +$2.00)",
            ),
        ]

    async def select_delivery_slot(self, slot_id: str) -> bool:
        slots = await self.list_delivery_slots()
        for s in slots:
            if s.slot_id == slot_id and s.is_available:
                self._selected_slot = s
                return True
        return False

    async def revalidate_cart(self, expected_quote: Any) -> CartDiff:
        if not self._cart_lines:
            return CartDiff(has_changes=False)
        current_cart = await self.read_cart()
        old_total = (
            expected_quote.gross_total_cents
            if hasattr(expected_quote, "gross_total_cents")
            else current_cart.gross_total_cents
        )
        if current_cart.gross_total_cents != old_total:
            return CartDiff(
                has_changes=True,
                price_changed=True,
                old_total_cents=old_total,
                new_total_cents=current_cart.gross_total_cents,
                detail="Cart total price changed during revalidation",
            )
        return CartDiff(has_changes=False, old_total_cents=old_total, new_total_cents=current_cart.gross_total_cents)

    async def submit_order(self, approval_token: str, slot_id: str = "") -> OrderConfirmation:
        raise NotImplementedError(
            "Live checkout is not yet implemented for FairPrice. "
            "No retailer order was placed and no confirmation number was generated."
        )
