from datetime import datetime
from uuid import UUID

from domain.models.core import ShoppingListItem, SubstitutionPolicy
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Shopping List & Item Schemas
# -----------------------------------------------------------------------------
class ShoppingListItemCreate(BaseModel):
    name: str
    category: str | None = None
    desired_quantity: float = 1.0
    unit_measure: str = "pack"
    min_pack_size: str | None = None
    max_pack_size: str | None = None
    must_have: bool = True
    is_enabled: bool = True
    substitution_policy: SubstitutionPolicy = SubstitutionPolicy.SAME_BRAND_ONLY
    preferred_brands: list[str] = []
    exclusions: list[str] = []
    pinned_skus: dict[str, str] = {}


class ShoppingListItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    desired_quantity: float | None = None
    unit_measure: str | None = None
    min_pack_size: str | None = None
    max_pack_size: str | None = None
    must_have: bool | None = None
    is_enabled: bool | None = None
    substitution_policy: SubstitutionPolicy | None = None
    preferred_brands: list[str] | None = None
    exclusions: list[str] | None = None
    pinned_skus: dict[str, str] | None = None


class ShoppingListCreate(BaseModel):
    name: str
    description: str | None = None
    items: list[ShoppingListItemCreate] = []


class ShoppingListRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[ShoppingListItem] = []


# -----------------------------------------------------------------------------
# Comparison Run & SSE Event Schemas
# -----------------------------------------------------------------------------
class ComparisonRunCreate(BaseModel):
    shopping_list_id: UUID
    target_retailers: list[str] = Field(
        default=["fairprice", "shengsiong", "littlefarms", "redmart"],
        alias="retailer_ids",
    )

    model_config = ConfigDict(populate_by_name=True)


class StoreEventResponse(BaseModel):
    retailer_id: str
    state: str
    from_state: str
    to_state: str
    progress_pct: int
    message: str = ""
    action_type: str | None = None
    resume_token: str | None = None
    event_id: str = ""
    timestamp: str = ""


# -----------------------------------------------------------------------------
# Quote & Approval Schemas
# -----------------------------------------------------------------------------
class QuoteLineRead(BaseModel):
    id: UUID
    quote_id: UUID
    shopping_item_id: UUID
    retailer_sku: str
    product_title: str
    product_brand: str | None = None
    product_url: str
    image_url: str | None = None
    pack_size: str | None = None
    requested_quantity: float
    packs_added: int
    is_in_stock: bool
    is_exact_match: bool
    is_substituted: bool = False
    missing_reason: str | None = None
    unit_price_cents: int
    unit_measure: str = "pack"
    line_total_cents: int


class StoreQuoteRead(BaseModel):
    id: UUID
    run_id: UUID
    retailer_id: str
    retailer_cart_id: str | None = None
    cart_url: str | None = None
    cart_fingerprint: str
    source_mode: str = "LIVE"
    currency: str = "SGD"
    subtotal_cents: int
    promotions_discount_cents: int = 0
    delivery_fee_cents: int = 0
    service_fee_cents: int = 0
    bag_fee_cents: int = 0
    slot_fee_cents: int = 0
    gross_total_cents: int
    derived_net_cents: int
    gst_cents: int
    free_delivery_threshold_cents: int | None = None
    eligible_subtotal_for_free_delivery_cents: int = 0
    amount_needed_for_free_delivery_cents: int = 0
    is_complete: bool = False
    is_all_items_complete: bool = False
    is_required_complete: bool = False
    requested_item_count: int = 0
    found_item_count: int = 0
    missing_item_count: int = 0
    missing_must_have_count: int = 0
    missing_required_count: int = 0
    selected_delivery_slot_id: str | None = None
    selected_delivery_slot_window: str | None = None
    expires_at: datetime
    created_at: datetime
    lines: list[QuoteLineRead] = []


class ApprovalCreate(BaseModel):
    quote_id: UUID
    delivery_slot_id: str
    idempotency_key: str | None = None


class QuoteApproveRequest(BaseModel):
    delivery_slot_id: str
    idempotency_key: str | None = None


class SelectSlotRequest(BaseModel):
    slot_id: str


class ResumeStoreRequest(BaseModel):
    resume_token: str


class OrderSubmitRequest(BaseModel):
    approval_token: str
