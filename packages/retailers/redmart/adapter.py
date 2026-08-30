import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from apps.browser_worker.live_driver import LiveRetailerDriver
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


class RedMartAdapter(RetailerAdapter):
    retailer_id = "redmart"

    def __init__(self, session_profile_dir: str | None = None):
        sm = SessionManager()
        self.session_profile_dir = session_profile_dir or str(sm.get_profile_path(self.retailer_id))
        self._cart_lines: dict[str, CartLine] = {}
        self._selected_slot: DeliverySlot | None = None
        self._live_driver = LiveRetailerDriver(session_manager=sm)

    async def check_session(self) -> SessionStatus:
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_rm_{uuid4().hex[:8]}",
                detail="RedMart / Lazada session profile not initialized.",
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> CandidateProduct | None:
        if not sku or not sku.startswith("RM_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"RedMart Item {sku}",
            brand="RedMart",
            category="Groceries",
            price_cents=610,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=305,
            product_url=f"https://www.lazada.sg/products/{sku}.html",
            image_url=f"https://images.lazada.sg/{sku}.jpg",
            in_stock=True,
            is_exact_match=True,
        )

    async def search_candidates(self, query: str, category_hint: str | None = None) -> list[CandidateProduct]:
        clean_query = query.lower().strip()
        candidates: list[CandidateProduct] = []

        # 1. Live Online Search
        try:
            live_items = await self._live_driver.search_redmart(clean_query)
        except Exception:
            live_items = []
        for item in live_items:
            is_excluded, _ = is_excluded_by_negative_filter(item.title, category=item.category)
            if is_excluded:
                continue
            candidates.append(
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku=item.retailer_sku,
                    title=item.title,
                    brand=item.brand,
                    category=item.category,
                    price_cents=item.price_cents,
                    pack_size=item.pack_size,
                    unit_measure=item.unit_measure,
                    unit_price_cents=item.unit_price_cents,
                    product_url=item.product_url,
                    image_url=item.image_url,
                    in_stock=item.in_stock,
                    is_exact_match=True,
                )
            )

        # 2. MOCK_FIXTURE — for offline/test use only.
        # In live runs (ALLOW_MOCK_FALLBACK != true) a search miss is a hard failure.
        if not candidates:
            if os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() != "true":
                raise RuntimeError(
                    f"LIVE_RUN_MOCK_BLOCKED: RedMart live search returned no results for '{query}'. "
                    "Set ALLOW_MOCK_FALLBACK=true only in test environments."
                )
            catalog = [
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_405060",
                    title="Meiji Fresh Milk 2L (RedMart)",
                    brand="Meiji",
                    category="Dairy & Chilled",
                    price_cents=625,
                    pack_size="2L",
                    unit_measure="L",
                    unit_price_cents=312,
                    product_url="https://www.lazada.sg/products/meiji-milk-2l-405060.html",
                    image_url="https://images.lazada.sg/405060.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_412233",
                    title="Chew's Fresh Eggs with Vitamin E 10s",
                    brand="Chew's",
                    category="Eggs",
                    price_cents=350,
                    pack_size="10s",
                    unit_measure="pack",
                    unit_price_cents=350,
                    product_url="https://www.lazada.sg/products/chews-eggs-10s-412233.html",
                    image_url="https://images.lazada.sg/412233.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_423344",
                    title="RedMart Fresh Meyer Lemons 3s Pack",
                    brand="RedMart",
                    category="Produce",
                    price_cents=260,
                    pack_size="3s",
                    unit_measure="pack",
                    unit_price_cents=86,
                    product_url="https://www.lazada.sg/products/redmart-lemons-423344.html",
                    image_url="https://images.lazada.sg/423344.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_433445",
                    title="San Pellegrino Sparkling Natural Mineral Water 1L",
                    brand="San Pellegrino",
                    category="Beverages",
                    price_cents=310,
                    pack_size="1L",
                    unit_measure="L",
                    unit_price_cents=310,
                    product_url="https://www.lazada.sg/products/san-pellegrino-1l-433445.html",
                    image_url="https://images.lazada.sg/433445.jpg",
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
        unit_price = 350
        title = f"RedMart Item {sku}"
        if "405060" in sku or "milk" in sku.lower():
            unit_price = 625
            title = "Meiji Fresh Milk 2L (RedMart)"
        elif "423344" in sku or "lemon" in sku.lower():
            unit_price = 260
            title = "RedMart Fresh Meyer Lemons 3s Pack"
        elif "433445" in sku or "water" in sku.lower():
            unit_price = 310
            title = "San Pellegrino Sparkling Natural Mineral Water 1L"

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
        threshold = 6000  # $60.00 free delivery
        delivery_fee = 0 if subtotal >= threshold else 599
        service_fee = 99
        bag_fee = 0
        slot_fee = self._selected_slot.fee_cents if self._selected_slot else 0
        gross = subtotal + delivery_fee + service_fee + bag_fee + slot_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_rm_{uuid4().hex[:8]}",
            cart_url="https://www.lazada.sg/cart",
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
                slot_id="slot_rm_1",
                start_time=now + timedelta(hours=16),
                end_time=now + timedelta(hours=18),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 10:00 AM - 12:00 PM (Standard)",
            ),
            DeliverySlot(
                slot_id="slot_rm_2",
                start_time=now + timedelta(hours=20),
                end_time=now + timedelta(hours=22),
                fee_cents=199,
                is_available=True,
                display_label="Tomorrow 02:00 PM - 04:00 PM (Priority +$1.99)",
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
            "Live checkout is not yet implemented for RedMart. "
            "No retailer order was placed and no confirmation number was generated."
        )
