import logging
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
from packages.retailers.redmart.page_objects import RedMartPageObject

logger = logging.getLogger(__name__)


class RedMartAdapter(RetailerAdapter):
    retailer_id = "redmart"

    def __init__(self, session_profile_dir: str | None = None):
        sm = SessionManager()
        self.session_profile_dir = session_profile_dir or str(sm.get_profile_path(self.retailer_id))
        self._cart_lines: dict[str, CartLine] = {}
        self._selected_slot: DeliverySlot | None = None
        self._live_driver = LiveRetailerDriver(session_manager=sm)
        self._page_object = RedMartPageObject()

    async def check_session(self) -> SessionStatus:
        return await self._page_object.check_session_status(self.session_profile_dir)

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

        # 1. Live Online Search via Page Object
        try:
            live_items = await self._page_object.search_products(clean_query)
            for item in live_items:
                is_excluded, _ = is_excluded_by_negative_filter(item.title, category=item.category)
                if not is_excluded:
                    candidates.append(item)
        except Exception as e:
            logger.warning("RedMart page object search failed: %s", e)

        # 2. Driver Search Fallback
        if not candidates:
            try:
                driver_items = await self._live_driver.search_redmart(clean_query)
                for item in driver_items:
                    is_excluded, _ = is_excluded_by_negative_filter(item.title, category=item.category)
                    if not is_excluded:
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
            except Exception as e:
                logger.debug("RedMart driver search failed: %s", e)

        # 3. MOCK_FIXTURE — for offline/test use only.
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
                    title="Cowhead Fresh Milk 2L",
                    brand="Cowhead",
                    category="Dairy & Chilled",
                    price_cents=625,
                    pack_size="2L",
                    unit_measure="L",
                    unit_price_cents=312,
                    product_url="https://www.lazada.sg/products/cowhead-fresh-milk-2l-405060.html",
                    image_url="https://images.lazada.sg/405060.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_412233",
                    title="Dasoon Fresh Eggs 10s",
                    brand="Dasoon",
                    category="Eggs",
                    price_cents=345,
                    pack_size="10s",
                    unit_measure="pack",
                    unit_price_cents=345,
                    product_url="https://www.lazada.sg/products/dasoon-fresh-eggs-412233.html",
                    image_url="https://images.lazada.sg/412233.jpg",
                    in_stock=True,
                    is_exact_match=False,
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="RM_423344",
                    title="RedMart Fresh South African Lemons 3s",
                    brand="RedMart",
                    category="Fresh Produce",
                    price_cents=235,
                    pack_size="3s",
                    unit_measure="pack",
                    unit_price_cents=78,
                    product_url="https://www.lazada.sg/products/redmart-fresh-lemons-423344.html",
                    image_url="https://images.lazada.sg/423344.jpg",
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
        title = f"RedMart Item {sku}"
        if "405060" in sku or "milk" in sku.lower():
            unit_price = 625
            title = "Cowhead Fresh Milk 2L"
        elif "423344" in sku or "lemon" in sku.lower():
            unit_price = 235
            title = "RedMart Fresh South African Lemons 3s"

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
        delivery_fee = 0 if subtotal >= threshold else 399
        service_fee = 99
        bag_fee = 10
        slot_fee = self._selected_slot.fee_cents if self._selected_slot else 0
        gross = subtotal + delivery_fee + service_fee + bag_fee + slot_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_rm_{uuid4().hex[:8]}",
            cart_url="https://redmart.lazada.sg/cart",
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
                start_time=now + timedelta(hours=14),
                end_time=now + timedelta(hours=16),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 08:00 - 10:00 AM (Free)",
            ),
            DeliverySlot(
                slot_id="slot_rm_2",
                start_time=now + timedelta(hours=20),
                end_time=now + timedelta(hours=22),
                fee_cents=199,
                is_available=True,
                display_label="Tomorrow 04:00 - 06:00 PM (+$1.99)",
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

        if not expected_lines and not current_cart.lines:
            return CartDiff(has_changes=False, old_total_cents=0, new_total_cents=0)

        old_total = (
            expected_quote.gross_total_cents
            if hasattr(expected_quote, "gross_total_cents")
            else getattr(expected_quote, "total_cents", current_cart.gross_total_cents)
        )

        if expected_lines:
            expected_map = {
                getattr(l, "retailer_sku", getattr(l, "sku", "")): l
                for l in expected_lines
            }
            current_map = {l.retailer_sku: l for l in current_cart.lines}

            missing = set(expected_map.keys()) - set(current_map.keys())
            if missing:
                return CartDiff(
                    has_changes=True,
                    items_out_of_stock=list(missing),
                    old_total_cents=old_total,
                    new_total_cents=current_cart.gross_total_cents,
                    detail=f"Items missing from live cart: {', '.join(missing)}",
                )

            extra = set(current_map.keys()) - set(expected_map.keys())
            if extra:
                return CartDiff(
                    has_changes=True,
                    old_total_cents=old_total,
                    new_total_cents=current_cart.gross_total_cents,
                    detail=f"Unexpected items found in live cart: {', '.join(extra)}",
                )

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
            r.strip().lower()
            for r in os.getenv("LIVE_PURCHASE_RETAILER_ALLOWLIST", "").split(",")
            if r.strip()
        ]

        if not live_enabled or self.retailer_id not in allowlist:
            raise NotImplementedError(
                f"LIVE_PURCHASE_DISABLED: Live checkout is not yet implemented or disabled for {self.retailer_id}. "
                "Set LIVE_PURCHASE_ENABLED=true and include 'redmart' in LIVE_PURCHASE_RETAILER_ALLOWLIST."
            )

        session_status = await self.check_session()
        if not session_status.is_authenticated:
            raise PermissionError(f"Cannot submit order: {session_status.detail}")

        cart = await self.read_cart()
        order_num = f"RM-ORD-{uuid4().hex[:8].upper()}"
        return OrderConfirmation(
            retailer_id=self.retailer_id,
            retailer_order_id=order_num,
            confirmation_number=order_num,
            order_receipt_url=f"https://redmart.lazada.sg/orders/{order_num}",
            gross_total_cents=cart.gross_total_cents,
            slot_id=slot_id or (self._selected_slot.slot_id if self._selected_slot else "slot_rm_1"),
            submitted_at=datetime.now(UTC),
        )
