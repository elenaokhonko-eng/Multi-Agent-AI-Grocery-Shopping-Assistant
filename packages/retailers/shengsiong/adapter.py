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


class ShengSiongAdapter(RetailerAdapter):
    retailer_id = "shengsiong"

    def __init__(self, session_profile_dir: Optional[str] = None):
        self.session_profile_dir = session_profile_dir or os.path.expanduser("~/.profiles/shengsiong")
        self._cart_lines: Dict[str, CartLine] = {}
        self._selected_slot: Optional[DeliverySlot] = None

    async def check_session(self) -> SessionStatus:
        if not os.path.exists(self.session_profile_dir):
            return SessionStatus(
                is_authenticated=False,
                requires_action=True,
                action_type="LOGIN_REQUIRED",
                resume_token=f"res_ss_{uuid4().hex[:8]}",
                detail="Sheng Siong session profile not initialized. Please authenticate manually."
            )
        return SessionStatus(is_authenticated=True, user_name="Elena")

    async def resolve_pinned_sku(self, sku: str) -> Optional[CandidateProduct]:
        if not sku or not sku.startswith("SS_"):
            return None
        return CandidateProduct(
            store_id=self.retailer_id,
            retailer_sku=sku,
            title=f"Sheng Siong Pinned Item {sku}",
            brand="Sheng Siong",
            category="Groceries",
            price_cents=595,
            pack_size="2L",
            unit_measure="L",
            unit_price_cents=298,
            product_url=f"https://allforyou.sg/product/{sku}",
            image_url=f"https://images.allforyou.sg/{sku}.jpg",
            in_stock=True,
            is_exact_match=True
        )

    async def search_candidates(self, query: str, category_hint: Optional[str] = None) -> List[CandidateProduct]:
        candidates: List[CandidateProduct] = []
        clean_query = query.lower().strip()

        if "milk" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="SS_203040",
                title="Meiji Fresh Milk 2L (Sheng Siong)",
                brand="Meiji",
                category="Dairy & Chilled",
                price_cents=610,
                pack_size="2L",
                unit_measure="L",
                unit_price_cents=305,
                product_url="https://allforyou.sg/product/meiji-fresh-milk-2l-203040",
                image_url="https://images.allforyou.sg/203040.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "egg" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="SS_212223",
                title="Chew's Fresh Eggs 10s (Sheng Siong)",
                brand="Chew's",
                category="Eggs",
                price_cents=330,
                pack_size="10s",
                unit_measure="pack",
                unit_price_cents=330,
                product_url="https://allforyou.sg/product/chews-fresh-eggs-212223",
                image_url="https://images.allforyou.sg/212223.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        elif "lemon" in clean_query:
            # High-fidelity Sheng Siong candidates including non-produce noise to test exclusion gate
            candidates.extend([
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="SS_223344",
                    title="Fresh South African Lemons 3s",
                    brand="FreshProduce",
                    category="Fruits & Vegetables",
                    price_cents=195,
                    pack_size="3s",
                    unit_measure="pack",
                    unit_price_cents=195,
                    product_url="https://allforyou.sg/product/fresh-lemons-223344",
                    image_url="https://images.allforyou.sg/223344.jpg",
                    in_stock=True,
                    is_exact_match=True
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="SS_NOISE_01",
                    title="Lemon Dishwashing Liquid Detergent 1L",
                    brand="Sunlight",
                    category="Household & Cleaning",
                    price_cents=290,
                    pack_size="1L",
                    unit_measure="L",
                    unit_price_cents=290,
                    product_url="https://allforyou.sg/product/sunlight-lemon-dishwashing",
                    in_stock=True,
                    is_exact_match=False
                ),
                CandidateProduct(
                    store_id=self.retailer_id,
                    retailer_sku="SS_NOISE_02",
                    title="Lemon Tea 6x250ml",
                    brand="Pokka",
                    category="Beverages",
                    price_cents=360,
                    pack_size="6s",
                    unit_measure="pack",
                    unit_price_cents=360,
                    product_url="https://allforyou.sg/product/pokka-lemon-tea",
                    in_stock=True,
                    is_exact_match=False
                )
            ])
        elif "water" in clean_query:
            candidates.append(CandidateProduct(
                store_id=self.retailer_id,
                retailer_sku="SS_241516",
                title="San Pellegrino Sparkling Mineral Water 1L",
                brand="San Pellegrino",
                category="Beverages",
                price_cents=310,
                pack_size="1L",
                unit_measure="L",
                unit_price_cents=310,
                product_url="https://allforyou.sg/product/san-pellegrino-241516",
                image_url="https://images.allforyou.sg/241516.jpg",
                in_stock=True,
                is_exact_match=True
            ))
        return candidates

    def validate_candidate(self, candidate: CandidateProduct, desired_item: Dict[str, Any]) -> bool:
        # Mandatory: Lemons reject detergent, tea, beer, toiletries, cleaning products (SS-07)
        hard_exclusions = ["detergent", "dishwashing", "tea", "beer", "toiletries", "cleaning", "bleach", "shampoo"]
        user_exclusions = desired_item.get("exclusions", [])
        all_exclusions = set(hard_exclusions + [e.lower() for e in user_exclusions])

        for exc in all_exclusions:
            if re.search(rf"\b{re.escape(exc)}\b", candidate.title, re.IGNORECASE) or (
                candidate.category and re.search(rf"\b{re.escape(exc)}\b", candidate.category, re.IGNORECASE)
            ):
                candidate.rejection_reason = f"Excluded keyword matched: {exc}"
                return False

        # Category gate
        if desired_item.get("category") == "Produce" and candidate.category:
            if "Household" in candidate.category or "Cleaning" in candidate.category:
                candidate.rejection_reason = f"Wrong category: {candidate.category}"
                return False

        return True

    async def add_exact_item(self, sku: str, quantity: int) -> bool:
        self._cart_lines[sku] = CartLine(
            retailer_sku=sku,
            title=f"Sheng Siong Item {sku}",
            quantity=quantity,
            unit_price_cents=310,
            line_total_cents=310 * quantity
        )
        return True

    async def read_cart(self) -> AuthoritativeCart:
        lines = list(self._cart_lines.values())
        subtotal = sum(l.line_total_cents for l in lines)
        delivery_fee = 0 if subtotal >= 6000 else 400
        gross = subtotal + delivery_fee

        return AuthoritativeCart(
            retailer_id=self.retailer_id,
            cart_id=f"cart_ss_{uuid4().hex[:6]}",
            cart_url="https://allforyou.sg/cart",
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
                slot_id="slot_ss_morning",
                start_time=now + timedelta(days=1, hours=1),
                end_time=now + timedelta(days=1, hours=3),
                fee_cents=0,
                is_available=True,
                display_label="Tomorrow 08:30 - 10:30 (Free)"
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
        order_num = f"SS-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        return OrderConfirmation(
            retailer_order_id=order_num,
            confirmed_total_cents=cart.gross_total_cents,
            delivery_slot=self._selected_slot.display_label if self._selected_slot else "Morning Slot",
            receipt_url=f"https://allforyou.sg/receipts/{order_num}"
        )
