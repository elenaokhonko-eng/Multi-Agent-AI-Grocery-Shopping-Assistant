import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from apps.browser_worker.live_driver import LiveRetailerDriver
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


class LittleFarmsAdapter(RetailerAdapter):
    retailer_id = "littlefarms"

    def __init__(self, session_profile_dir: str | None = None):
        self.session_profile_dir = session_profile_dir or os.path.expanduser("~/.profiles/littlefarms")
        self._cart_lines: dict[str, CartLine] = {}
        self._selected_slot: DeliverySlot | None = None
        self._live_driver = LiveRetailerDriver()

    async def check_session(self) -> SessionStatus:
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_lf_{uuid4().hex[:8]}",
                detail="Little Farms session profile not initialized.",
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> CandidateProduct | None:
        if not sku or not sku.startswith("LF_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"Little Farms Item {sku}",
            brand="Little Farms",
            category="Organic",
            price_cents=850,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=425,
            product_url=f"https://littlefarms.com/products/{sku}",
            image_url=f"https://images.littlefarms.com/{sku}.jpg",
            in_stock=True,
            is_exact_match=True,
        )

    async def search_candidates(self, query: str, category_hint: str | None = None) -> list[CandidateProduct]:
        clean_query = query.lower().strip()
        candidates: list[CandidateProduct] = []

        # 1. Live Online Search
        live_items = await self._live_driver.search_littlefarms(clean_query)
        for item in live_items:
            is_excluded, _ = is_excluded_by_negative_filter(item.title, category=item.category)
            if is_excluded:
                continue
            candidates.append(CandidateProduct(
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
            ))

        # 2. MOCK_FIXTURE — for offline/test use only.
        # In live runs (ALLOW_MOCK_FALLBACK != true) a search miss is a hard failure.
        if not candidates:
            if os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() != "true":
                raise RuntimeError(
                    f"LIVE_RUN_MOCK_BLOCKED: Little Farms live search returned no results for '{query}'. "
                    "Set ALLOW_MOCK_FALLBACK=true only in test environments."
                )
            catalog = [
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="LF_304050",
                    title="Barambah Organics Pure Whole Milk 2L",
                    brand="Barambah Organics",
                    category="Dairy",
                    price_cents=950,
                    pack_size="2L",
                    unit_measure="L",
                    unit_price_cents=475,
                    product_url="https://littlefarms.com/products/barambah-milk-2l",
                    image_url="https://images.littlefarms.com/barambah.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="LF_312233",
                    title="Honest Eggs Co. Pasture Raised Free Range Eggs 10s",
                    brand="Honest Eggs Co.",
                    category="Eggs",
                    price_cents=895,
                    pack_size="10s",
                    unit_measure="pack",
                    unit_price_cents=895,
                    product_url="https://littlefarms.com/products/honest-eggs-10s",
                    image_url="https://images.littlefarms.com/eggs.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="LF_323344",
                    title="Organic Fresh Lemons 3s",
                    brand="Little Farms Organic",
                    category="Fresh Produce",
                    price_cents=495,
                    pack_size="3s",
                    unit_measure="pack",
                    unit_price_cents=165,
                    product_url="https://littlefarms.com/products/organic-lemons-3s",
                    image_url="https://images.littlefarms.com/lemons.jpg",
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
        unit_price = 895
        title = f"Little Farms Item {sku}"
        if "304050" in sku or "milk" in sku.lower():
            unit_price = 950
            title = "Barambah Organics Pure Whole Milk 2L"
        elif "323344" in sku or "lemon" in sku.lower():
            unit_price = 495
            title = "Organic Fresh Lemons 3s"

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
        threshold = 10000  # $100.00 free delivery
        delivery_fee = 0 if subtotal >= threshold else 1200
        service_fee = 0
        bag_fee = 0
        slot_fee = self._selected_slot.fee_cents if self._selected_slot else 0
        gross = subtotal + delivery_fee + service_fee + bag_fee + slot_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_lf_{uuid4().hex[:8]}",
            cart_url="https://littlefarms.com/cart",
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
                slot_id="slot_lf_standard",
                start_time=now + timedelta(hours=24),
                end_time=now + timedelta(hours=28),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow Next-Day Courier (Free)",
            )
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
        old_total = expected_quote.gross_total_cents if hasattr(expected_quote, "gross_total_cents") else current_cart.gross_total_cents
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
            "Live checkout is not yet implemented for Little Farms. "
            "No retailer order was placed and no confirmation number was generated."
        )
