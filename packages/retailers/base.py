from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionStatus(BaseModel):
    is_authenticated: bool
    user_name: Optional[str] = None
    requires_action: bool = False
    action_type: Optional[str] = None  # "LOGIN_EXPIRED", "CAPTCHA", "OTP", "ACCOUNT_ALERT"
    resume_token: Optional[str] = None
    detail: Optional[str] = None


class CandidateProduct(BaseModel):
    store_id: str
    retailer_sku: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    price_cents: int
    pack_size: Optional[str] = None
    unit_measure: str = "pack"
    unit_price_cents: int = 0
    image_url: Optional[str] = None
    product_url: str
    in_stock: bool = True
    is_exact_match: bool = False
    rejection_reason: Optional[str] = None


class CartLine(BaseModel):
    retailer_sku: str
    title: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    is_unowned: bool = False


class AuthoritativeCart(BaseModel):
    retailer_id: str
    cart_id: Optional[str] = None
    cart_url: Optional[str] = None
    lines: List[CartLine] = Field(default_factory=list)
    subtotal_cents: int = 0
    delivery_fee_cents: int = 0
    service_fee_cents: int = 0
    bag_fee_cents: int = 0
    slot_fee_cents: int = 0
    gross_total_cents: int = 0
    free_delivery_threshold_cents: Optional[int] = None
    unowned_items_detected: bool = False


class DeliverySlot(BaseModel):
    slot_id: str
    start_time: datetime
    end_time: datetime
    fee_cents: int = 0
    is_available: bool = True
    display_label: str


class CartDiff(BaseModel):
    has_changes: bool = False
    price_changed: bool = False
    old_total_cents: int = 0
    new_total_cents: int = 0
    items_out_of_stock: List[str] = Field(default_factory=list)
    items_price_changed: List[Dict[str, Any]] = Field(default_factory=list)
    slot_changed: bool = False
    detail: Optional[str] = None


class OrderConfirmation(BaseModel):
    retailer_order_id: str
    confirmed_total_cents: int
    delivery_slot: str
    receipt_url: Optional[str] = None
    is_uncertain: bool = False
    placed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RetailerAdapter(ABC):
    retailer_id: str

    @abstractmethod
    async def check_session(self) -> SessionStatus:
        """Verify session validity or return USER_ACTION_REQUIRED."""

    @abstractmethod
    async def resolve_pinned_sku(self, sku: str) -> Optional[CandidateProduct]:
        """Directly retrieve product by exact pinned SKU ID."""

    @abstractmethod
    async def search_candidates(self, query: str, category_hint: Optional[str] = None) -> List[CandidateProduct]:
        """Search top-N candidates from store catalog."""

    def validate_candidate(self, candidate: CandidateProduct, desired_item: Dict[str, Any]) -> bool:
        """Apply deterministic brand, pack, unit, and exclusion gates."""
        return True

    async def add_item_to_cart(self, sku: str, quantity: int) -> bool:
        """Add item to retailer cart."""
        return await self.add_exact_item(sku, quantity)

    async def add_exact_item(self, sku: str, quantity: int) -> bool:
        """Compatibility alias for add_item_to_cart."""
        return True

    @abstractmethod
    async def read_cart(self) -> AuthoritativeCart:
        """Read authoritative basket lines and fees directly from store."""

    @abstractmethod
    async def list_delivery_slots(self) -> List[DeliverySlot]:
        """Fetch available delivery slots."""

    @abstractmethod
    async def select_delivery_slot(self, slot_id: str) -> bool:
        """Select delivery slot in retailer checkout session."""

    @abstractmethod
    async def revalidate_cart(self, expected_quote: Any) -> CartDiff:
        """Re-read cart prior to submission and compare against fingerprint or quote."""

    @abstractmethod
    async def submit_order(self, approval_token: str, slot_id: str = "") -> OrderConfirmation:
        """Execute final checkout click when live ordering is enabled."""
