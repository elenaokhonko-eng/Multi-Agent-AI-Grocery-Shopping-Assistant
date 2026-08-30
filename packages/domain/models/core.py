from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class SubstitutionPolicy(str, Enum):
    SAME_BRAND_ONLY = "SAME_BRAND_ONLY"
    SAME_CATEGORY_ANY_BRAND = "SAME_CATEGORY_ANY_BRAND"
    CHEAPEST_ALTERNATIVE = "CHEAPEST_ALTERNATIVE"
    NO_SUBSTITUTIONS = "NO_SUBSTITUTIONS"


class ShoppingList(SQLModel, table=True):
    __tablename__ = "shopping_lists"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    version: int = Field(default=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    items: list["ShoppingListItem"] = Relationship(
        back_populates="shopping_list", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    snapshots: list["ComparisonSnapshot"] = Relationship(
        back_populates="shopping_list", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ShoppingListItem(SQLModel, table=True):
    __tablename__ = "shopping_list_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_list_id: UUID = Field(foreign_key="shopping_lists.id", index=True)
    name: str
    category: str | None = None
    desired_quantity: float = Field(default=1.0, gt=0)
    unit_measure: str = Field(default="pack")  # "kg", "g", "L", "ml", "pack", "pieces"
    min_pack_size: str | None = None
    max_pack_size: str | None = None
    must_have: bool = Field(default=True)
    is_enabled: bool = Field(default=True)
    substitution_policy: SubstitutionPolicy = Field(default=SubstitutionPolicy.SAME_BRAND_ONLY)
    preferred_brands: list[str] = Field(default=[], sa_column=Column(JSON))
    exclusions: list[str] = Field(default=[], sa_column=Column(JSON))
    pinned_skus: dict[str, str] = Field(default={}, sa_column=Column(JSON))  # e.g. {"fairprice": "FP_123"}
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    shopping_list: ShoppingList = Relationship(back_populates="items")


class ComparisonSnapshot(SQLModel, table=True):
    __tablename__ = "comparison_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_list_id: UUID = Field(foreign_key="shopping_lists.id", index=True)
    list_version: int
    frozen_items_json: list[dict[str, Any]] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    shopping_list: ShoppingList = Relationship(back_populates="snapshots")
    runs: list["ComparisonRun"] = Relationship(
        back_populates="snapshot", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ComparisonRun(SQLModel, table=True):
    __tablename__ = "comparison_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(foreign_key="comparison_snapshots.id", index=True)
    status: str = Field(default="QUEUED", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    snapshot: ComparisonSnapshot = Relationship(back_populates="runs")
    quotes: list["StoreQuote"] = Relationship(
        back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    event_logs: list["StoreEventLog"] = Relationship(
        back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    tasks: list["RetailerTask"] = Relationship(
        back_populates="run", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class RetailerTask(SQLModel, table=True):
    __tablename__ = "retailer_tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="comparison_runs.id", index=True)
    retailer_id: str = Field(index=True)
    status: str = Field(default="QUEUED", index=True)  # QUEUED, CLAIMED, RUNNING, COMPLETED, FAILED, USER_ACTION_REQUIRED
    lease_token: str | None = Field(default=None, index=True)
    lease_expires_at: datetime | None = Field(default=None, index=True)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    run: ComparisonRun = Relationship(back_populates="tasks")


class RetailerSession(SQLModel, table=True):
    __tablename__ = "retailer_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    retailer_id: str = Field(unique=True, index=True)
    is_authenticated: bool = Field(default=False)
    user_name: str | None = None
    requires_action: bool = Field(default=False)
    action_type: str | None = None  # LOGIN_REQUIRED, CAPTCHA, OTP, ACCOUNT_ALERT
    resume_token: str | None = None
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StoreEventLog(SQLModel, table=True):
    __tablename__ = "store_event_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="comparison_runs.id", index=True)
    retailer_id: str = Field(index=True)
    from_state: str
    to_state: str
    progress_pct: int
    message: str
    action_type: str | None = None
    resume_token: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    run: ComparisonRun = Relationship(back_populates="event_logs")


class StoreQuote(SQLModel, table=True):
    __tablename__ = "store_quotes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="comparison_runs.id", index=True)
    retailer_id: str = Field(index=True)  # "fairprice", "shengsiong", "littlefarms", "redmart"
    retailer_cart_id: str | None = None
    cart_url: str | None = None
    cart_fingerprint: str = Field(index=True)
    source_mode: str = Field(default="LIVE")
    currency: str = Field(default="SGD")

    subtotal_cents: int
    promotions_discount_cents: int = Field(default=0)
    delivery_fee_cents: int = Field(default=0)
    service_fee_cents: int = Field(default=0)
    bag_fee_cents: int = Field(default=0)
    slot_fee_cents: int = Field(default=0)
    gross_total_cents: int
    derived_net_cents: int
    gst_cents: int

    free_delivery_threshold_cents: int | None = None
    eligible_subtotal_for_free_delivery_cents: int = Field(default=0)
    amount_needed_for_free_delivery_cents: int = Field(default=0)

    is_complete: bool = Field(default=False)
    is_all_items_complete: bool = Field(default=False)
    is_required_complete: bool = Field(default=False)
    requested_item_count: int = Field(default=0)
    found_item_count: int = Field(default=0)
    missing_item_count: int = Field(default=0)
    missing_must_have_count: int = Field(default=0)
    missing_required_count: int = Field(default=0)
    selected_delivery_slot_id: str | None = None
    selected_delivery_slot_window: str | None = None

    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    run: ComparisonRun = Relationship(back_populates="quotes")
    lines: list["QuoteLine"] = Relationship(
        back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    approvals: list["Approval"] = Relationship(
        back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    revisions: list["QuoteRevision"] = Relationship(
        back_populates="quote", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class QuoteRevision(SQLModel, table=True):
    __tablename__ = "quote_revisions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quote_id: UUID = Field(foreign_key="store_quotes.id", index=True)
    revision_number: int = Field(default=1)
    cart_fingerprint: str = Field(index=True)
    subtotal_cents: int
    gross_total_cents: int
    selected_delivery_slot_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    quote: StoreQuote = Relationship(back_populates="revisions")


class QuoteLine(SQLModel, table=True):
    __tablename__ = "quote_lines"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quote_id: UUID = Field(foreign_key="store_quotes.id", index=True)
    shopping_item_id: UUID = Field(index=True)
    retailer_sku: str
    product_title: str
    product_brand: str | None = None
    product_url: str
    image_url: str | None = None
    pack_size: str | None = None

    requested_quantity: float = Field(default=1.0)
    packs_added: int
    is_in_stock: bool
    is_exact_match: bool
    is_substituted: bool = Field(default=False)
    missing_reason: str | None = None

    unit_price_cents: int
    unit_measure: str = Field(default="pack")
    line_total_cents: int

    quote: StoreQuote = Relationship(back_populates="lines")


class Approval(SQLModel, table=True):
    __tablename__ = "approvals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quote_id: UUID = Field(foreign_key="store_quotes.id", index=True)
    approval_token: str = Field(unique=True, index=True)
    idempotency_key: str = Field(unique=True, index=True)
    delivery_slot_id: str
    expected_fingerprint: str
    is_used: bool = Field(default=False)
    approved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime

    quote: StoreQuote = Relationship(back_populates="approvals")
    receipt: Optional["OrderReceipt"] = Relationship(
        back_populates="approval", sa_relationship_kwargs={"uselist": False}
    )
    submission_attempts: list["SubmissionAttempt"] = Relationship(
        back_populates="approval", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class SubmissionAttempt(SQLModel, table=True):
    __tablename__ = "submission_attempts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    approval_id: UUID = Field(foreign_key="approvals.id", index=True)
    idempotency_key: str = Field(index=True)
    attempt_number: int = Field(default=1)
    status: str = Field(default="PENDING", index=True)  # PENDING, SUBMITTED, CONFIRMED, FAILED, UNCERTAIN
    retailer_response: str | None = None
    error_detail: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    approval: Approval = Relationship(back_populates="submission_attempts")


class OrderReceipt(SQLModel, table=True):
    __tablename__ = "order_receipts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    approval_id: UUID = Field(foreign_key="approvals.id", unique=True, index=True)
    retailer_order_id: str = Field(index=True)
    retailer_id: str
    confirmed_total_cents: int
    confirmed_delivery_slot: str
    receipt_url: str | None = None
    placed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    approval: Approval = Relationship(back_populates="receipt")


class UserProductCorrection(SQLModel, table=True):
    __tablename__ = "user_product_corrections"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_list_item_id: UUID | None = Field(default=None, foreign_key="shopping_list_items.id", index=True)
    shopping_item_name: str = Field(index=True)
    retailer_id: str = Field(index=True)
    preferred_sku: str
    preferred_title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
