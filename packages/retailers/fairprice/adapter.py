import os
import re
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


class FairPriceAdapter(RetailerAdapter):
    retailer_id = "fairprice"

    def __init__(self, session_profile_dir: Optional[str] = None):
        self.session_profile_dir = session_profile_dir or os.path.expanduser("~/.profiles/fairprice")
        self._cart_lines: Dict[str, CartLine] = {}
        self._selected_slot: Optional[DeliverySlot] = None

    async def check_session(self) -> SessionStatus:
        # Check if local session storage / profile exists
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_fp_{uuid4().hex[:8]}",
                detail="FairPrice session profile not initialized. Please run manual bootstrap login."
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> Optional[CandidateProduct]:
        # Exact pinned SKU resolver
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
            is_exact_match=True
        )

    async def search_candidates(self, query: str, category_hint: Optional[str] = None) -> List[CandidateProduct]:
        candidates: List[CandidateProduct] = []
        clean_query = query.lower().strip()

        # Deterministic product catalog mapping for FairPrice
        if "milk" in clean_query:
            candidates.append(CandidateProduct(
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
                is_exact_match=True
            ))
        elif "egg" in clean_query:
            candidates.append(CandidateProduct(
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
                is_exact_match=True
            ))
        elif "lemon" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="FP_123456",
                title="Fresh Lemons 3s Pack",
                brand="Pasar",
                category="Fresh Produce",
                price_cents=215,
                pack_size="3s",
                unit_measure="pack",
                unit_price_cents=215,
                product_url="https://www.fairprice.com.sg/product/fresh-lemons-123456",
                image_url="https://images.fairprice.com.sg/123456.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "water" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="FP_141516",
                title="San Pellegrino Sparkling Natural Mineral Water 1L",
                brand="San Pellegrino",
                category="Beverages",
                price_cents=320,
                pack_size="1L",
                unit_measure="L",
                unit_price_cents=320,
                product_url="https://www.fairprice.com.sg/product/san-pellegrino-141516",
                image_url="https://images.fairprice.com.sg/141516.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        return candidates

    def validate_candidate(self, candidate: CandidateProduct, desired_item: Dict[str, Any]) -> bool:
        # 1. Negative exclusions
        exclusions = desired_item.get("exclusions", [])
        for exc in exclusions:
            if re.search(rf"\b{re.escape(exc)}\b", candidate.title, re.IGNORECASE):
                candidate.rejection_reason = f"Excluded keyword matched: {exc}"
                return False

        # 2. Preferred brands
        preferred_brands = desired_item.get("preferred_brands", [])
        if preferred_brands and candidate.brand:
            if not any(b.lower() in candidate.brand.lower() or b.lower() in candidate.title.lower() for b in preferred_brands):
                # Brand mismatch
                if desired_item.get("substitution_policy") == "SAME_BRAND_ONLY":
                    candidate.rejection_reason = f"Brand {candidate.brand} not in preferred {preferred_brands}"
                    return False

        return True

    async def add_exact_item(self, sku: str, quantity: int) -> bool:
        line = CartLine(
            retailer_sku=sku,
            title=f"FairPrice Item {sku}",
            quantity=quantity,
            unit_price_cents=350,
            line_total_cents=350 * quantity
        )
        self._cart_lines[sku] = line
        return True

    async def read_cart(self) -> AuthoritativeCart:
        lines = list(self._cart_lines.values())
        subtotal = sum(l.line_total_cents for l in lines)
        delivery_fee = 0 if subtotal >= 7900 else 550
        service_fee = 0
        bag_fee = 20
        gross = subtotal + delivery_fee + service_fee + bag_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_fp_{uuid4().hex[:6]}",
            cart_url="https://www.fairprice.com.sg/cart",
            lines=lines,
            subtotal_cents=subtotal,
            delivery_fee_cents=delivery_fee,
            service_fee_cents=service_fee,
            bag_fee_cents=bag_fee,
            gross_total_cents=gross,
            free_delivery_threshold_cents=7900,
            unowned_items_detected=False
        )

    async def list_delivery_slots(self) -> List[DeliverySlot]:
        now = datetime.now(timezone.utc)
        return [
            DeliverySlot(
                slot_id="slot_fp_morning",
                start_time=now + timedelta(days=1, hours=2),
                end_time=now + timedelta(days=1, hours=4),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 09:00 - 11:00 (Free)"
            ),
            DeliverySlot(
                slot_id="slot_fp_afternoon",
                start_time=now + timedelta(days=1, hours=6),
                end_time=now + timedelta(days=1, hours=8),
                fee_cents=100,
                is_available=True,
                display_label="Tomorrow 13:00 - 15:00 (+S$1.00)"
            ),
        ]

    async def select_delivery_slot(self, slot_id: str) -> bool:
        slots = await self.list_delivery_slots()
        for s in slots:
            if s.slot_id == slot_id and s.is_available:
                self._selected_slot = s
                return True
        return False

    async def revalidate_cart(self, expected_fingerprint: str) -> CartDiff:
        cart = await self.read_cart()
        return CartDiff(
            has_changes=False,
            old_total_cents=cart.gross_total_cents,
            new_total_cents=cart.gross_total_cents
        )

    async def submit_order(self, approval_token: str) -> OrderConfirmation:
        cart = await self.read_cart()
        order_num = f"FP-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        return OrderConfirmation(
            retailer_order_id=order_num,
            confirmed_total_cents=cart.gross_total_cents,
            delivery_slot=self._selected_slot.display_label if self._selected_slot else "Standard Slot",
            receipt_url=f"https://www.fairprice.com.sg/receipts/{order_num}"
        )
