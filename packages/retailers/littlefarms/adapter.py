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


class LittleFarmsAdapter(RetailerAdapter):
    retailer_id = "littlefarms"

    def __init__(self, session_profile_dir: Optional[str] = None):
        self.session_profile_dir = session_profile_dir or os.path.expanduser("~/.profiles/littlefarms")
        self._cart_lines: Dict[str, CartLine] = {}
        self._selected_slot: Optional[DeliverySlot] = None

    async def check_session(self) -> SessionStatus:
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_lf_{uuid4().hex[:8]}",
                detail="Little Farms session profile not initialized. Please authenticate manually."
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> Optional[CandidateProduct]:
        if not sku or not sku.startswith("LF_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"Little Farms Organic Item {sku}",
            brand="Little Farms",
            category="Organic Groceries",
            price_cents=850,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=425,
            product_url=f"https://littlefarms.com/product/{sku}",
            image_url=f"https://images.littlefarms.com/{sku}.jpg",
            in_stock=True,
            is_exact_match=True
        )

    async def search_candidates(self, query: str, category_hint: Optional[str] = None) -> List[CandidateProduct]:
        candidates: List[CandidateProduct] = []
        clean_query = query.lower().strip()

        if "milk" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="LF_301020",
                title="Barambah Organics Pure Fresh Milk 2L",
                brand="Barambah Organics",
                category="Dairy & Chilled",
                price_cents=950,
                pack_size="2L",
                unit_measure="L",
                unit_price_cents=475,
                product_url="https://littlefarms.com/product/barambah-organics-milk-2l-301020",
                image_url="https://images.littlefarms.com/301020.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "egg" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="LF_312233",
                title="Honest Eggs Co. Free Range Eggs 10s",
                brand="Honest Eggs",
                category="Eggs",
                price_cents=820,
                pack_size="10s",
                unit_measure="pack",
                unit_price_cents=820,
                product_url="https://littlefarms.com/product/honest-eggs-10s-312233",
                image_url="https://images.littlefarms.com/312233.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "lemon" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="LF_323344",
                title="Organic Eureka Lemons 3s Pack",
                brand="Organic Choice",
                category="Fresh Produce",
                price_cents=495,
                pack_size="3s",
                unit_measure="pack",
                unit_price_cents=495,
                product_url="https://littlefarms.com/product/organic-lemons-323344",
                image_url="https://images.littlefarms.com/323344.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "water" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="LF_341516",
                title="San Pellegrino Sparkling Mineral Water 1L",
                brand="San Pellegrino",
                category="Beverages",
                price_cents=390,
                pack_size="1L",
                unit_measure="L",
                unit_price_cents=390,
                product_url="https://littlefarms.com/product/san-pellegrino-341516",
                image_url="https://images.littlefarms.com/341516.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        return candidates

    def validate_candidate(self, candidate: CandidateProduct, desired_item: Dict[str, Any]) -> bool:
        return True

    async def add_exact_item(self, sku: str, quantity: int) -> bool:
        self._cart_lines[sku] = CartLine(
            retailer_sku=sku,
            title=f"Little Farms Item {sku}",
            quantity=quantity,
            unit_price_cents=650,
            line_total_cents=650 * quantity
        )
        return True

    async def read_cart(self) -> AuthoritativeCart:
        lines = list(self._cart_lines.values())
        subtotal = sum(l.line_total_cents for l in lines)
        delivery_fee = 0 if subtotal >= 10000 else 1500  # S$100 threshold for Little Farms
        gross = subtotal + delivery_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_lf_{uuid4().hex[:6]}",
            cart_url="https://littlefarms.com/cart",
            lines=lines,
            subtotal_cents=subtotal,
            delivery_fee_cents=delivery_fee,
            service_fee_cents=0,
            bag_fee_cents=0,
            gross_total_cents=gross,
            free_delivery_threshold_cents=10000,
            unowned_items_detected=False
        )

    async def list_delivery_slots(self) -> List[DeliverySlot]:
        now = datetime.now(timezone.utc)
        return [
            DeliverySlot(
                slot_id="slot_lf_morning",
                start_time=now + timedelta(days=1, hours=3),
                end_time=now + timedelta(days=1, hours=5),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 10:00 - 12:00 (Free with S$100+)"
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
        order_num = f"LF-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        return OrderConfirmation(
            retailer_order_id=order_num,
            confirmed_total_cents=cart.gross_total_cents,
            delivery_slot=self._selected_slot.display_label if self._selected_slot else "Express Slot",
            receipt_url=f"https://littlefarms.com/receipts/{order_num}"
        )
