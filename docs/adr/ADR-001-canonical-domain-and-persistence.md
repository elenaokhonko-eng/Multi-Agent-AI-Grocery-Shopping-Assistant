# ADR-001: Canonical Domain Models & PostgreSQL Persistence Strategy

**Status:** APPROVED & FROZEN  
**Author:** Chief Architect (`fullstack-reviewer`)  
**Scope:** `packages/domain/**`, Database Migrations

---

## 1. Context & Motivation
Previous iterations suffered from fragmented database models, competing shopping list definitions, inconsistent integer/float money representation, missing modules (`domain.models.core`), and unsafe `create_all()` table creation in production.

This record freezes the canonical SQLModel / Pydantic domain models, standardizes money handling in integer cents (SGD), and establishes PostgreSQL + Alembic as the sole production persistence standard.

---

## 2. Canonical Domain Entities & Schema Definition

### 2.1 Currency & Money Rule
* **Standard:** All monetary values (`price`, `subtotal`, `delivery_fee`, `service_fee`, `slot_fee`, `gross_total`, `net_total`, `gst_amount`) MUST be stored as non-negative **integers representing cents in SGD** (e.g. `S$ 6.35` -> `635` cents).
* **GST Standard:** Singapore GST is strictly 9%. Derived net is calculated as `net_cents = round(gross_cents / 1.09)`. GST amount is `gross_cents - net_cents`.

---

### 2.2 Entity Models

```python
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel, Column, JSON


class SubstitutionPolicy(str, Enum):
    SAME_BRAND_ONLY = "SAME_BRAND_ONLY"
    SAME_CATEGORY_ANY_BRAND = "SAME_CATEGORY_ANY_BRAND"
    CHEAPEST_ALTERNATIVE = "CHEAPEST_ALTERNATIVE"
    NO_SUBSTITUTIONS = "NO_SUBSTITUTIONS"


class ShoppingList(SQLModel, table=True):
    __tablename__ = "shopping_lists"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    version: int = Field(default=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    items: List["ShoppingListItem"] = Relationship(back_populates="shopping_list")
    snapshots: List["ComparisonSnapshot"] = Relationship(back_populates="shopping_list")


class ShoppingListItem(SQLModel, table=True):
    __tablename__ = "shopping_list_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_list_id: UUID = Field(foreign_key="shopping_lists.id", index=True)
    name: str
    category: Optional[str] = None
    desired_quantity: int = Field(default=1, ge=1)
    unit_measure: str = Field(default="pack")  # "kg", "g", "L", "ml", "pack", "pieces"
    min_pack_size: Optional[str] = None
    max_pack_size: Optional[str] = None
    must_have: bool = Field(default=True)
    is_enabled: bool = Field(default=True)
    substitution_policy: SubstitutionPolicy = Field(default=SubstitutionPolicy.SAME_BRAND_ONLY)
    preferred_brands: List[str] = Field(default=[], sa_column=Column(JSON))
    exclusions: List[str] = Field(default=[], sa_column=Column(JSON))
    pinned_skus: Dict[str, str] = Field(default={}, sa_column=Column(JSON))  # e.g. {"fairprice": "FP_123"}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    shopping_list: ShoppingList = Relationship(back_populates="items")


class ComparisonSnapshot(SQLModel, table=True):
    __tablename__ = "comparison_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_list_id: UUID = Field(foreign_key="shopping_lists.id", index=True)
    list_version: int
    frozen_items_json: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    shopping_list: ShoppingList = Relationship(back_populates="snapshots")
    runs: List["ComparisonRun"] = Relationship(back_populates="snapshot")


class ComparisonRun(SQLModel, table=True):
    __tablename__ = "comparison_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    snapshot_id: UUID = Field(foreign_key="comparison_snapshots.id", index=True)
    status: str = Field(default="QUEUED", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    snapshot: ComparisonSnapshot = Relationship(back_populates="runs")
    quotes: List["StoreQuote"] = Relationship(back_populates="run")


class StoreQuote(SQLModel, table=True):
    __tablename__ = "store_quotes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="comparison_runs.id", index=True)
    retailer_id: str = Field(index=True)  # "fairprice", "shengsiong", "littlefarms", "redmart"
    retailer_cart_id: Optional[str] = None
    cart_url: Optional[str] = None
    cart_fingerprint: str = Field(index=True)
    
    subtotal_cents: int
    promotions_discount_cents: int = Field(default=0)
    delivery_fee_cents: int = Field(default=0)
    service_fee_cents: int = Field(default=0)
    bag_fee_cents: int = Field(default=0)
    slot_fee_cents: int = Field(default=0)
    gross_total_cents: int
    derived_net_cents: int
    gst_cents: int
    
    free_delivery_threshold_cents: Optional[int] = None
    amount_needed_for_free_delivery_cents: int = Field(default=0)
    
    is_complete: bool = Field(default=False)
    missing_must_have_count: int = Field(default=0)
    selected_delivery_slot_id: Optional[str] = None
    selected_delivery_slot_window: Optional[str] = None
    
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    run: ComparisonRun = Relationship(back_populates="quotes")
    lines: List["QuoteLine"] = Relationship(back_populates="quote")
    approvals: List["Approval"] = Relationship(back_populates="quote")


class QuoteLine(SQLModel, table=True):
    __tablename__ = "quote_lines"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quote_id: UUID = Field(foreign_key="store_quotes.id", index=True)
    shopping_item_id: UUID = Field(index=True)
    retailer_sku: str
    product_title: str
    product_brand: Optional[str] = None
    product_url: str
    image_url: Optional[str] = None
    pack_size: Optional[str] = None
    
    requested_quantity: int
    packs_added: int
    is_in_stock: bool
    is_exact_match: bool
    is_substituted: bool = Field(default=False)
    missing_reason: Optional[str] = None
    
    unit_price_cents: int
    unit_measure: str
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
    approved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    quote: StoreQuote = Relationship(back_populates="approvals")
    receipt: Optional["OrderReceipt"] = Relationship(back_populates="approval")


class OrderReceipt(SQLModel, table=True):
    __tablename__ = "order_receipts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    approval_id: UUID = Field(foreign_key="approvals.id", unique=True, index=True)
    retailer_order_id: str = Field(index=True)
    retailer_id: str
    confirmed_total_cents: int
    confirmed_delivery_slot: str
    receipt_url: Optional[str] = None
    placed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    approval: Approval = Relationship(back_populates="receipt")


class UserProductCorrection(SQLModel, table=True):
    __tablename__ = "user_product_corrections"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shopping_item_name: str = Field(index=True)
    retailer_id: str = Field(index=True)
    preferred_sku: str
    preferred_title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## 3. Persistence Strategy
1. **Production Database:** PostgreSQL (via `psycopg` / `asyncpg`).
2. **Migrations:** Managed exclusively with Alembic under `packages/domain/alembic/`.
   - `env.py` must import `SQLModel` and `domain.models.core`.
   - `env.py` must read `os.getenv("DATABASE_URL")` with fallback to local connection strings.
   - `SQLModel.metadata.create_all()` is strictly banned in production startup hooks.
3. **Local Testing:** SQLite (`sqlite:///./test.db`) permitted strictly for unit and contract tests in `tests/`.
