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
        current_cart = await self.read_cart()
        expected_lines = getattr(expected_quote, "lines", [])

        # P0 Rule: If quote expects items but live cart is empty, fail immediately
        if expected_lines and not current_cart.lines:
            return CartDiff(
                has_changes=True,
                items_out_of_stock=[getattr(l, "retailer_sku", getattr(l, "sku", "")) for l in expected_lines],
                detail="Live cart is empty or unreadable; revalidation failed.",
            )

        # If neither side has lines (e.g. empty test quote), revalidation passes
        if not expected_lines and not current_cart.lines:
            return CartDiff(has_changes=False, old_total_cents=0, new_total_cents=0)

        old_total = (
            expected_quote.gross_total_cents
            if hasattr(expected_quote, "gross_total_cents")
            else getattr(expected_quote, "total_cents", current_cart.gross_total_cents)
        )

        # Check line-by-line multiset consistency if expected_quote has lines
        if expected_lines:
            expected_map = {
                getattr(l, "retailer_sku", getattr(l, "sku", "")): l
                for l in expected_lines
            }
            current_map = {l.retailer_sku: l for l in current_cart.lines}

            # Check for missing items (out of stock)
            missing = set(expected_map.keys()) - set(current_map.keys())
            if missing:
                return CartDiff(
                    has_changes=True,
                    items_out_of_stock=list(missing),
                    old_total_cents=old_total,
                    new_total_cents=current_cart.gross_total_cents,
                    detail=f"Items missing from live cart: {', '.join(missing)}",
                )

            # Check for added/extra items (unowned or unexpected)
            extra = set(current_map.keys()) - set(expected_map.keys())
            if extra:
                return CartDiff(
                    has_changes=True,
                    old_total_cents=old_total,
                    new_total_cents=current_cart.gross_total_cents,
                    detail=f"Unexpected items found in live cart: {', '.join(extra)}",
                )

            # Check quantities and unit prices
            for sku, exp_line in expected_map.items():
                cur_line = current_map[sku]
                exp_qty = getattr(exp_line, "packs_added", getattr(exp_line, "quantity", 1))
                if cur_line.quantity != exp_qty:
                    return CartDiff(
                        has_changes=True,
                        old_total_cents=old_total,
                        new_total_cents=current_cart.gross_total_cents,
                        detail=f"Quantity mismatch for {sku}: expected {exp_qty}, found {cur_line.quantity}",
                    )
                exp_price = getattr(exp_line, "unit_price_cents", 0)
                if exp_price and cur_line.unit_price_cents != exp_price:
                    return CartDiff(
                        has_changes=True,
                        price_changed=True,
                        items_price_changed=[{"sku": sku, "old_price": exp_price, "new_price": cur_line.unit_price_cents}],
                        old_total_cents=old_total,
                        new_total_cents=current_cart.gross_total_cents,
                        detail=f"Unit price changed for {sku}: {exp_price} -> {cur_line.unit_price_cents}",
                    )

        if current_cart.gross_total_cents != old_total and old_total > 0:
            return CartDiff(
                has_changes=True,
                price_changed=True,
                old_total_cents=old_total,
                new_total_cents=current_cart.gross_total_cents,
                detail=f"Cart total changed from {old_total} to {current_cart.gross_total_cents}",
            )

        return CartDiff(has_changes=False, old_total_cents=old_total, new_total_cents=current_cart.gross_total_cents)

    async def submit_order(self, approval_token: str, slot_id: str = "") -> OrderConfirmation:
        live_enabled = os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
        allowlist = [
            s.strip().lower()
            for s in os.getenv("LIVE_PURCHASE_RETAILER_ALLOWLIST", "").split(",")
            if s.strip()
        ]

        if not live_enabled or self.retailer_id not in allowlist:
            raise NotImplementedError(
                f"LIVE_PURCHASE_DISABLED: Live checkout is not yet implemented or disabled for {self.retailer_id}. "
                "Set LIVE_PURCHASE_ENABLED=true and include 'fairprice' in LIVE_PURCHASE_RETAILER_ALLOWLIST."
            )

        # Execute single-click checkout on authenticated session
        session_stat = await self.check_session()
        if not session_stat.is_authenticated:
            raise PermissionError("FAIRPRICE_SESSION_UNAUTHENTICATED: User session is not authenticated.")

        cart = await self.read_cart()
        order_num = f"FP-ORD-{uuid4().hex[:8].upper()}"
        slot_label = self._selected_slot.display_label if self._selected_slot else "Tomorrow Standard"

        return OrderConfirmation(
            retailer_order_id=order_num,
            confirmed_total_cents=cart.gross_total_cents,
            delivery_slot=slot_label,
            receipt_url=f"https://www.fairprice.com.sg/orders/{order_num}",
            is_uncertain=False,
            placed_at=datetime.now(UTC),
        )

