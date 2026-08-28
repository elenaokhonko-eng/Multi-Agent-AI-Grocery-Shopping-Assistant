import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

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

    def __init__(self, session_profile_dir: Optional[str] = None):
        self.session_profile_dir = session_profile_dir or os.path.expanduser("~/.profiles/redmart")
        self._cart_lines: Dict[str, CartLine] = {}
        self._selected_slot: Optional[DeliverySlot] = None

    async def check_session(self) -> SessionStatus:
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_rm_{uuid4().hex[:8]}",
                detail="RedMart / Lazada session profile not initialized. Please authenticate manually."
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> Optional[CandidateProduct]:
        if not sku or not sku.startswith("RM_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"RedMart Fulfilled Item {sku}",
            brand="RedMart",
            category="Groceries",
            price_cents=625,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=312,
            product_url=f"https://www.lazada.sg/products/redmart-{sku}.html",
            image_url=f"https://images.lazada.sg/rm/{sku}.jpg",
            in_stock=True,
            is_exact_match=True
        )

    async def search_candidates(self, query: str, category_hint: Optional[str] = None) -> List[CandidateProduct]:
        candidates: List[CandidateProduct] = []
        clean_query = query.lower().strip()

        # Strict RedMart channel fulfilment only (reject general 3rd party marketplace items)
        if "milk" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="RM_401020",
                title="Meiji Fresh Milk 2L (RedMart Fulfilled)",
                brand="Meiji",
                category="Dairy & Chilled",
                price_cents=625,
                pack_size="2L",
                unit_measure="L",
                unit_price_cents=312,
                product_url="https://www.lazada.sg/products/redmart-meiji-milk-2l-401020.html",
                image_url="https://images.lazada.sg/rm/401020.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "egg" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="RM_412233",
                title="Chew's Fresh Eggs with Vitamin E 10s (RedMart)",
                brand="Chew's",
                category="Eggs",
                price_cents=350,
                pack_size="10s",
                unit_measure="pack",
                unit_price_cents=350,
                product_url="https://www.lazada.sg/products/redmart-chews-eggs-412233.html",
                image_url="https://images.lazada.sg/rm/412233.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "lemon" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="RM_423344",
                title="RedMart Fresh Lemons 3s",
                brand="RedMart Fresh",
                category="Fresh Produce",
                price_cents=220,
                pack_size="3s",
                unit_measure="pack",
                unit_price_cents=220,
                product_url="https://www.lazada.sg/products/redmart-lemons-423344.html",
                image_url="https://images.lazada.sg/rm/423344.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "water" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="RM_441516",
                title="San Pellegrino Sparkling Mineral Water 1L",
                brand="San Pellegrino",
                category="Beverages",
                price_cents=315,
                pack_size="1L",
                unit_measure="L",
                unit_price_cents=315,
                product_url="https://www.lazada.sg/products/redmart-san-pellegrino-441516.html",
                image_url="https://images.lazada.sg/rm/441516.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        return candidates

    def validate_candidate(self, candidate: CandidateProduct, desired_item: Dict[str, Any]) -> bool:
        return True

    async def add_exact_item(self, sku: str, quantity: int) -> bool:
        self._cart_lines[sku] = CartLine(
            retailer_sku=sku,
            title=f"RedMart Item {sku}",
            quantity=quantity,
            unit_price_cents=340,
            line_total_cents=340 * quantity
        )
        return True

    async def read_cart(self) -> AuthoritativeCart:
        lines = list(self._cart_lines.values())
        subtotal = sum(l.line_total_cents for l in lines)
        delivery_fee = 0 if subtotal >= 6000 else 599  # S$60 threshold for RedMart
        gross = subtotal + delivery_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_rm_{uuid4().hex[:6]}",
            cart_url="https://www.lazada.sg/cart",
            lines=lines,
            subtotal_cents=subtotal,
            delivery_fee_cents=delivery_fee,
            service_fee_cents=0,
            bag_fee_cents=0,
            gross_total_cents=gross,
            free_delivery_threshold_cents=6000,
            unowned_items_detected=False
        )

    async def list_delivery_slots(self) -> List[DeliverySlot]:
        now = datetime.now(timezone.utc)
        return [
            DeliverySlot(
                slot_id="slot_rm_morning",
                start_time=now + timedelta(days=1, hours=2),
                end_time=now + timedelta(days=1, hours=4),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 09:00 - 11:00 (RedMart Standard)"
            )
        ]

    async def select_delivery_slot(self, slot_id: str) -> bool:
        self._selected_slot = (await self.list_delivery_slots())[0]
        return True

    async def revalidate_cart(self, expected_fingerprint: str) -> CartDiff:
        cart = await self.read_cart()
        return CartDiff(
            has_changes=False,
            old_total_cents=cart.gross_total_cents,
            new_total_cents=cart.gross_total_cents
        )

    async def submit_order(self, approval_token: str) -> OrderConfirmation:
        cart = await self.read_cart()
        order_num = f"RM-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        return OrderConfirmation(
            retailer_order_id=order_num,
            confirmed_total_cents=cart.gross_total_cents,
            delivery_slot=self._selected_slot.display_label if self._selected_slot else "RedMart Slot",
            receipt_url=f"https://www.lazada.sg/receipts/{order_num}"
        )
