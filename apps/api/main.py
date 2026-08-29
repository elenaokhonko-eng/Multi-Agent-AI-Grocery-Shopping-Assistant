import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from domain.models.core import (
    Approval,
    ComparisonRun,
    ComparisonSnapshot,
    OrderReceipt,
    QuoteLine,
    ShoppingList,
    ShoppingListItem,
    StoreEventLog,
    StoreQuote,
    SubstitutionPolicy,
)
from domain.services.fingerprint import compute_quote_fingerprint
from domain.services.matching import match_product_candidate
from domain.services.pricing import calculate_gst_inclusive
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from orchestration.state_machine import StateMachine, StoreState, StoreStateEvent
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, SQLModel, create_engine, select

from packages.retailers import (
    FairPriceAdapter,
    LittleFarmsAdapter,
    RedMartAdapter,
    RetailerAdapter,
    ShengSiongAdapter,
)

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./grocery.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# Adapter Registry
ADAPTER_MAP: dict[str, type[RetailerAdapter]] = {
    "fairprice": FairPriceAdapter,
    "shengsiong": ShengSiongAdapter,
    "littlefarms": LittleFarmsAdapter,
    "redmart": RedMartAdapter,
}

# In-memory SSE event bus per comparison run
RUN_EVENT_QUEUES: dict[str, list[asyncio.Queue]] = {}


def broadcast_run_event(run_id: str, event: StoreStateEvent, session: Session | None = None):
    # 1. Broadcast to active SSE queues
    queues = RUN_EVENT_QUEUES.get(run_id, [])
    for q in queues:
        q.put_nowait(event)

    # 2. Persist event to durable database log
    try:
        from_st = str(event.from_state.value if isinstance(event.from_state, StoreState) else (event.from_state or event.state.value if isinstance(event.state, StoreState) else event.state))
        to_st = str(event.to_state.value if isinstance(event.to_state, StoreState) else (event.to_state or event.state.value if isinstance(event.state, StoreState) else event.state))

        def persist(s: Session):
            db_event = StoreEventLog(
                run_id=UUID(run_id),
                retailer_id=event.retailer_id,
                from_state=from_st,
                to_state=to_st,
                progress_pct=event.progress_pct,
                message=event.detail or "",
                action_type=event.challenge_type,
                resume_token=event.resume_token,
                created_at=datetime.now(UTC),
            )
            s.add(db_event)
            s.commit()

        if session:
            persist(session)
        else:
            with Session(engine) as s:
                persist(s)
    except Exception as e:
        logger.warning("Failed to persist StoreEventLog for run %s: %s", run_id, e)


# -----------------------------------------------------------------------------
# Lifespan / Startup Handler
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    if DATABASE_URL.startswith("sqlite"):
        SQLModel.metadata.create_all(engine)
        # Ensure default shopping list exists
        with Session(engine) as session:
            lists = session.exec(select(ShoppingList)).all()
            if not lists:
                default_list = ShoppingList(
                    name="Weekly Groceries",
                    description="Standard Singapore weekly grocery essentials",
                    version=1,
                    is_active=True,
                )
                session.add(default_list)
                session.commit()
                session.refresh(default_list)

                default_items = [
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Milk",
                        category="Dairy & Chilled",
                        desired_quantity=2,
                        unit_measure="L",
                        must_have=True,
                        preferred_brands=["Meiji"],
                        exclusions=["soy", "almond", "powder"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Eggs",
                        category="Eggs",
                        desired_quantity=10,
                        unit_measure="pieces",
                        must_have=True,
                        preferred_brands=["Dasoon", "Chew's", "Honest Eggs Co."],
                        exclusions=["salted", "century"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Lemons",
                        category="Fresh Produce",
                        desired_quantity=3,
                        unit_measure="pieces",
                        must_have=True,
                        preferred_brands=[],
                        exclusions=["dishwash", "cleaner", "detergent", "tea", "soap"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Sparkling Water",
                        category="Beverages",
                        desired_quantity=1,
                        unit_measure="L",
                        must_have=False,
                        preferred_brands=["San Pellegrino"],
                        exclusions=["flavored", "sweetened"],
                    ),
                ]
                for item in default_items:
                    session.add(item)
                session.commit()

    yield


# -----------------------------------------------------------------------------
# FastAPI Application
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Multi-Agent AI Grocery Assistant Control Plane",
    version="2.0.0",
    description="Singapore Multi-Store Grocery Comparison, Rebalancing & Ordering Platform",
    lifespan=lifespan,
)

_cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Idempotency-Key"],
)


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class ShoppingListItemCreate(BaseModel):
    name: str
    category: str | None = None
    desired_quantity: int = 1
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
    desired_quantity: int | None = None
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


class ComparisonRunCreate(BaseModel):
    shopping_list_id: UUID
    target_retailers: list[str] = Field(
        default=["fairprice", "shengsiong", "littlefarms", "redmart"],
        alias="retailer_ids"
    )

    model_config = ConfigDict(populate_by_name=True)


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


# -----------------------------------------------------------------------------
# Health & Status
# -----------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check(session: Session = Depends(get_session)):
    live_enabled = os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
    db_status = "healthy"
    try:
        session.exec(select(ShoppingList).limit(1)).first()
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "live_purchase_enabled": live_enabled,
        "live_purchasing_enabled": live_enabled,
    }


# -----------------------------------------------------------------------------
# Shopping List Endpoints
# -----------------------------------------------------------------------------
@app.get("/shopping-lists", response_model=list[ShoppingListRead], tags=["Shopping Lists"])
def list_shopping_lists(session: Session = Depends(get_session)):
    lists = session.exec(select(ShoppingList).where(ShoppingList.is_active)).all()
    results = []
    for sl in lists:
        items = session.exec(select(ShoppingListItem).where(ShoppingListItem.shopping_list_id == sl.id)).all()
        results.append(ShoppingListRead(
            id=sl.id,
            name=sl.name,
            description=sl.description,
            version=sl.version,
            is_active=sl.is_active,
            created_at=sl.created_at,
            updated_at=sl.updated_at,
            items=list(items),
        ))
    return results


@app.get("/shopping-lists/{list_id}", response_model=ShoppingListRead, tags=["Shopping Lists"])
def get_shopping_list(list_id: UUID, session: Session = Depends(get_session)):
    slist = session.get(ShoppingList, list_id)
    if not slist or not slist.is_active:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    items = session.exec(select(ShoppingListItem).where(ShoppingListItem.shopping_list_id == list_id)).all()
    return ShoppingListRead(
        id=slist.id,
        name=slist.name,
        description=slist.description,
        version=slist.version,
        is_active=slist.is_active,
        created_at=slist.created_at,
        updated_at=slist.updated_at,
        items=list(items),
    )


@app.post("/shopping-lists", response_model=ShoppingListRead, status_code=status.HTTP_201_CREATED, tags=["Shopping Lists"])
def create_shopping_list(payload: ShoppingListCreate, session: Session = Depends(get_session)):
    slist = ShoppingList(name=payload.name, description=payload.description)
    session.add(slist)
    session.commit()
    session.refresh(slist)

    created_items = []
    for item_data in payload.items:
        item = ShoppingListItem(shopping_list_id=slist.id, **item_data.model_dump())
        session.add(item)
        created_items.append(item)
    session.commit()
    session.refresh(slist)
    return ShoppingListRead(
        id=slist.id,
        name=slist.name,
        description=slist.description,
        version=slist.version,
        is_active=slist.is_active,
        created_at=slist.created_at,
        updated_at=slist.updated_at,
        items=created_items,
    )


@app.post("/shopping-lists/{list_id}/items", response_model=ShoppingListItem, status_code=status.HTTP_201_CREATED, tags=["Shopping Lists"])
def add_item_to_list(list_id: UUID, payload: ShoppingListItemCreate, session: Session = Depends(get_session)):
    slist = session.get(ShoppingList, list_id)
    if not slist or not slist.is_active:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    item = ShoppingListItem(shopping_list_id=list_id, **payload.model_dump())
    slist.version += 1
    slist.updated_at = datetime.now(UTC)
    session.add(slist)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.patch("/shopping-lists/{list_id}/items/{item_id}", response_model=ShoppingListItem, tags=["Shopping Lists"])
def update_item_in_list(list_id: UUID, item_id: UUID, payload: ShoppingListItemUpdate, session: Session = Depends(get_session)):
    slist = session.get(ShoppingList, list_id)
    if not slist or not slist.is_active:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(item, k, v)

    item.updated_at = datetime.now(UTC)
    slist.version += 1
    slist.updated_at = datetime.now(UTC)
    session.add(slist)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/shopping-lists/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Shopping Lists"])
def delete_item_from_list(list_id: UUID, item_id: UUID, session: Session = Depends(get_session)):
    slist = session.get(ShoppingList, list_id)
    if not slist or not slist.is_active:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    session.delete(item)
    slist.version += 1
    slist.updated_at = datetime.now(UTC)
    session.add(slist)
    session.commit()


# -----------------------------------------------------------------------------
# Comparison Runs & Orchestration Engine
# -----------------------------------------------------------------------------
async def execute_live_retailer_worker(
    arg1: str | None = None,
    arg2: str | None = None,
    items: list[dict[str, Any]] | None = None,
    session_factory=None,
    adapter_override: RetailerAdapter | None = None,
    retailer_id: str | None = None,
    run_id: str | None = None,
):
    """Background worker executing real store search, authoritative cart and delivery slot retrieval."""
    # Resolve retailer_id and run_id from either positional or keyword arguments
    if retailer_id is None or run_id is None:
        if arg1 in ADAPTER_MAP or (adapter_override and getattr(adapter_override, "retailer_id", None) == arg1):
            retailer_id = retailer_id or arg1
            run_id = run_id or arg2
        else:
            run_id = run_id or arg1
            retailer_id = retailer_id or arg2

    if items is None:
        items = []

    if not retailer_id or not run_id:
        return

    adapter_cls = ADAPTER_MAP.get(retailer_id)
    adapter = adapter_override or (adapter_cls() if adapter_cls else None)
    if not adapter:
        return

    def get_db_session():
        if session_factory is None:
            return Session(engine)
        try:
            return session_factory()
        except TypeError:
            return session_factory(engine)

    def on_event(event: StoreStateEvent):
        broadcast_run_event(run_id, event)

    sm = StateMachine(str(run_id), retailer_id, event_callback=on_event)

    try:
        # 1. Session Validation
        await sm.transition(StoreState.SESSION_CHECK, progress_pct=15, detail="Checking store session")
        session_status = await adapter.check_session()
        if session_status.requires_action:
            await sm.transition(
                StoreState.USER_ACTION_REQUIRED,
                progress_pct=20,
                detail=session_status.detail or "User authentication required",
                challenge_type=session_status.action_type,
                resume_token=session_status.resume_token,
            )
            return

        # 2. Search & Product Matching
        await sm.transition(StoreState.SEARCHING, progress_pct=35, detail=f"Searching catalog for {len(items)} items")
        matched_lines: list[dict[str, Any]] = []
        all_must_haves_found = True
        missing_must_have_count = 0

        for item in items:
            pinned_sku = (item.get("pinned_skus") or {}).get(retailer_id)
            candidate = None
            if pinned_sku:
                candidate = await adapter.resolve_pinned_sku(pinned_sku)

            if not candidate:
                candidates = await adapter.search_candidates(item["name"], item.get("category"))
                for c in candidates:
                    is_match, _packs_needed, _rej_reason = match_product_candidate(
                        candidate_title=c.title,
                        candidate_sku=c.retailer_sku,
                        candidate_brand=c.brand,
                        candidate_category=c.category,
                        candidate_pack=c.pack_size,
                        item_spec=item,
                    )
                    if is_match and c.in_stock:
                        candidate = c
                        break

            if candidate and candidate.in_stock:
                desired_qty = item.get("desired_quantity", 1)
                is_match, packs_to_add, _ = match_product_candidate(
                    candidate_title=candidate.title,
                    candidate_sku=candidate.retailer_sku,
                    candidate_brand=candidate.brand,
                    candidate_category=candidate.category,
                    candidate_pack=candidate.pack_size,
                    item_spec=item,
                )
                packs = max(1, packs_to_add)
                await adapter.add_item_to_cart(candidate.retailer_sku, packs)
                line_total = candidate.price_cents * packs
                matched_lines.append({
                    "shopping_item_id": UUID(item["id"]) if isinstance(item["id"], str) else item["id"],
                    "retailer_sku": candidate.retailer_sku,
                    "product_title": candidate.title,
                    "product_brand": candidate.brand,
                    "product_url": candidate.product_url,
                    "image_url": candidate.image_url,
                    "pack_size": candidate.pack_size or "Standard",
                    "requested_quantity": desired_qty,
                    "packs_added": packs,
                    "is_in_stock": True,
                    "is_exact_match": candidate.is_exact_match,
                    "is_substituted": not candidate.is_exact_match,
                    "missing_reason": None,
                    "unit_price_cents": candidate.price_cents,
                    "unit_measure": candidate.unit_measure,
                    "line_total_cents": line_total,
                })
            else:
                if item.get("must_have", True):
                    all_must_haves_found = False
                    missing_must_have_count += 1
                matched_lines.append({
                    "shopping_item_id": UUID(item["id"]) if isinstance(item["id"], str) else item["id"],
                    "retailer_sku": "NOT_FOUND",
                    "product_title": f"{item['name']} (Out of Stock / No Match)",
                    "product_brand": None,
                    "product_url": "",
                    "image_url": None,
                    "pack_size": None,
                    "requested_quantity": item.get("desired_quantity", 1),
                    "packs_added": 0,
                    "is_in_stock": False,
                    "is_exact_match": False,
                    "is_substituted": False,
                    "missing_reason": "No valid in-stock product match found",
                    "unit_price_cents": 0,
                    "unit_measure": item.get("unit_measure", "pack"),
                    "line_total_cents": 0,
                })

        await sm.transition(StoreState.MATCHING, progress_pct=60, detail="Matching completed")

        # 3. Read Authoritative Cart
        await sm.transition(StoreState.CART_PREPARING, progress_pct=75, detail="Populating basket")
        cart = await adapter.read_cart()
        await sm.transition(StoreState.CART_READING, progress_pct=90, detail="Reading authoritative basket & fees")

        if cart.unowned_items_detected:
            await sm.transition(
                StoreState.BLOCKED,
                progress_pct=90,
                detail="Cart conflict: unowned items detected in retailer cart",
                error_code="CART_CONFLICT",
            )
            return

        # 4. List Delivery Slots & Select Default
        slots = await adapter.list_delivery_slots()
        default_slot = slots[0] if slots else None
        if default_slot:
            await adapter.select_delivery_slot(default_slot.slot_id)

        # 5. Persist Authoritative Quote
        with get_db_session() as session:
            subtotal_cents = cart.subtotal_cents
            fees_total = cart.delivery_fee_cents + cart.service_fee_cents + cart.bag_fee_cents + cart.slot_fee_cents
            gross_total = subtotal_cents + fees_total
            tax_info = calculate_gst_inclusive(gross_total)

            slot_id_val = default_slot.slot_id if default_slot else "default_slot"
            fingerprint = compute_quote_fingerprint(
                retailer_id=retailer_id,
                lines=matched_lines,
                delivery_slot_id=slot_id_val,
                subtotal_cents=subtotal_cents,
                fees_total_cents=fees_total,
                gross_total_cents=gross_total,
            )

            db_quote = StoreQuote(
                run_id=UUID(run_id),
                retailer_id=retailer_id,
                retailer_cart_id=cart.cart_id or f"cart_{retailer_id}_{uuid4().hex[:6]}",
                cart_url=cart.cart_url or f"https://www.{retailer_id}.com.sg/cart",
                cart_fingerprint=fingerprint,
                subtotal_cents=subtotal_cents,
                promotions_discount_cents=0,
                delivery_fee_cents=cart.delivery_fee_cents,
                service_fee_cents=cart.service_fee_cents,
                bag_fee_cents=cart.bag_fee_cents,
                slot_fee_cents=cart.slot_fee_cents,
                gross_total_cents=gross_total,
                derived_net_cents=tax_info["net_cents"],
                gst_cents=tax_info["gst_cents"],
                free_delivery_threshold_cents=cart.free_delivery_threshold_cents,
                amount_needed_for_free_delivery_cents=max(0, (cart.free_delivery_threshold_cents or 0) - subtotal_cents),
                is_complete=all_must_haves_found,
                missing_must_have_count=missing_must_have_count,
                selected_delivery_slot_id=slot_id_val,
                selected_delivery_slot_window=default_slot.display_label if default_slot else "Standard Window",
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
            session.add(db_quote)
            session.commit()
            session.refresh(db_quote)

            for line_data in matched_lines:
                ql = QuoteLine(quote_id=db_quote.id, **line_data)
                session.add(ql)
            session.commit()

        await sm.transition(
            StoreState.QUOTED,
            progress_pct=100,
            quote_id=str(db_quote.id),
            detail="Quote generated and verified",
        )

    except Exception as exc:
        await sm.transition(StoreState.FAILED, progress_pct=100, detail=str(exc), error_code="WORKER_EXCEPTION")


@app.post("/comparison-runs", response_model=dict[str, Any], status_code=status.HTTP_202_ACCEPTED, tags=["Comparison"])
async def start_comparison_run(payload: ComparisonRunCreate, session: Session = Depends(get_session)):
    slist = session.get(ShoppingList, payload.shopping_list_id)
    if not slist or not slist.is_active:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    items = session.exec(
        select(ShoppingListItem)
        .where(ShoppingListItem.shopping_list_id == payload.shopping_list_id)
        .where(ShoppingListItem.is_enabled)
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="Cannot run comparison on empty shopping list")

    frozen_items = [
        {
            "id": str(i.id),
            "name": i.name,
            "category": i.category,
            "desired_quantity": i.desired_quantity,
            "unit_measure": i.unit_measure,
            "min_pack_size": i.min_pack_size,
            "max_pack_size": i.max_pack_size,
            "must_have": i.must_have,
            "substitution_policy": i.substitution_policy.value,
            "preferred_brands": i.preferred_brands or [],
            "exclusions": i.exclusions or [],
            "pinned_skus": i.pinned_skus or {},
        }
        for i in items
    ]

    snapshot = ComparisonSnapshot(
        shopping_list_id=slist.id,
        list_version=slist.version,
        frozen_items_json=frozen_items,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    crun = ComparisonRun(snapshot_id=snapshot.id, status="RUNNING")
    session.add(crun)
    session.commit()
    session.refresh(crun)

    run_id_str = str(crun.id)
    RUN_EVENT_QUEUES[run_id_str] = []

    # Launch parallel store workers with completion tracking
    async def coordinate_workers():
        worker_tasks = [
            execute_live_retailer_worker(
                retailer_id=r_id,
                run_id=run_id_str,
                items=frozen_items,
            )
            for r_id in payload.target_retailers
        ]
        await asyncio.gather(*worker_tasks, return_exceptions=True)
        try:
            with Session(engine) as s:
                run_rec = s.get(ComparisonRun, UUID(run_id_str))
                if run_rec:
                    quotes_found = s.exec(select(StoreQuote).where(StoreQuote.run_id == UUID(run_id_str))).all()
                    run_rec.status = "COMPLETED" if quotes_found else "FAILED"
                    s.add(run_rec)
                    s.commit()
        except Exception as coord_err:
            logger.warning("Error updating comparison run %s status: %s", run_id_str, coord_err)

    asyncio.create_task(coordinate_workers())

    return {
        "run_id": crun.id,
        "snapshot_id": snapshot.id,
        "status": "QUEUED",
        "retailers": payload.target_retailers,
        "created_at": crun.created_at.isoformat(),
    }


@app.get("/comparison-runs/{run_id}", tags=["Comparison"])
def get_comparison_run(run_id: UUID, session: Session = Depends(get_session)):
    crun = session.get(ComparisonRun, run_id)
    if not crun:
        raise HTTPException(status_code=404, detail="Comparison run not found")

    quotes = session.exec(select(StoreQuote).where(StoreQuote.run_id == run_id)).all()
    quote_summaries = []
    for q in quotes:
        lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == q.id)).all()
        quote_summaries.append({
            "quote_id": q.id,
            "retailer_id": q.retailer_id,
            "subtotal_cents": q.subtotal_cents,
            "promotions_discount_cents": q.promotions_discount_cents,
            "delivery_fee_cents": q.delivery_fee_cents,
            "service_fee_cents": q.service_fee_cents,
            "bag_fee_cents": q.bag_fee_cents,
            "slot_fee_cents": q.slot_fee_cents,
            "gross_total_cents": q.gross_total_cents,
            "gst_cents": q.gst_cents,
            "free_delivery_threshold_cents": q.free_delivery_threshold_cents,
            "amount_needed_for_free_delivery_cents": q.amount_needed_for_free_delivery_cents,
            "is_complete": q.is_complete,
            "missing_must_have_count": q.missing_must_have_count,
            "selected_delivery_slot_id": q.selected_delivery_slot_id,
            "selected_delivery_slot_window": q.selected_delivery_slot_window,
            "cart_url": q.cart_url,
            "lines": [
                {
                    "shopping_item_id": line.shopping_item_id,
                    "retailer_sku": line.retailer_sku,
                    "product_title": line.product_title,
                    "product_brand": line.product_brand,
                    "product_url": line.product_url,
                    "image_url": line.image_url,
                    "pack_size": line.pack_size,
                    "requested_quantity": line.requested_quantity,
                    "packs_added": line.packs_added,
                    "is_in_stock": line.is_in_stock,
                    "is_exact_match": line.is_exact_match,
                    "is_substituted": line.is_substituted,
                    "missing_reason": line.missing_reason,
                    "unit_price_cents": line.unit_price_cents,
                    "unit_measure": line.unit_measure,
                    "line_total_cents": line_total,
                }
                for line in lines
                for line_total in [line.line_total_cents]
            ],
        })

    complete_quotes = [q for q in quotes if q.is_complete]
    cheapest_complete_store = None
    if complete_quotes:
        best_q = min(complete_quotes, key=lambda x: x.gross_total_cents)
        cheapest_complete_store = best_q.retailer_id

    return {
        "run_id": crun.id,
        "snapshot_id": crun.snapshot_id,
        "status": crun.status,
        "created_at": crun.created_at.isoformat(),
        "quotes": quote_summaries,
        "cheapest_complete_store": cheapest_complete_store,
    }


@app.get("/comparison-runs/{run_id}/events", tags=["Comparison"])
async def stream_comparison_events(run_id: UUID, request: Request, session: Session = Depends(get_session)):
    """Resilient SSE stream: Replays historical events from DB before streaming live events."""
    run_id_str = str(run_id)

    # 1. Fetch historical event logs from database
    historical_logs = session.exec(
        select(StoreEventLog)
        .where(StoreEventLog.run_id == run_id)
        .order_by(StoreEventLog.created_at.asc())
    ).all()

    queue: asyncio.Queue = asyncio.Queue()
    if run_id_str not in RUN_EVENT_QUEUES:
        RUN_EVENT_QUEUES[run_id_str] = []
    RUN_EVENT_QUEUES[run_id_str].append(queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Replay historical events from DB (fields: retailer_id, from_state, to_state, state is not stored separately)
            for log in historical_logs:
                try:
                    evt = {
                        "retailer_id": log.retailer_id,
                        "state": log.to_state,
                        "from_state": log.from_state,
                        "to_state": log.to_state,
                        "progress_pct": log.progress_pct,
                        "detail": log.message,
                        "challenge_type": log.action_type,
                        "resume_token": log.resume_token,
                        "timestamp": log.created_at.isoformat(),
                    }
                    yield f"data: {json.dumps(evt)}\n\n"
                except Exception as replay_err:
                    logger.warning("SSE historical replay error for run %s: %s", run_id_str, replay_err)

            # Stream real-time events
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event: StoreStateEvent = await asyncio.wait_for(queue.get(), timeout=1.0)
                    try:
                        evt = {
                            "retailer_id": event.retailer_id,
                            "state": event.state,
                            "from_state": event.state,  # StoreStateEvent carries current state only
                            "to_state": event.state,
                            "progress_pct": event.progress_pct,
                            "detail": event.detail,
                            "challenge_type": event.challenge_type,
                            "resume_token": event.resume_token,
                            "timestamp": event.timestamp.isoformat(),
                        }
                        yield f"data: {json.dumps(evt)}\n\n"
                    except Exception as ser_err:
                        logger.warning("SSE serialization error for run %s: %s", run_id_str, ser_err)
                except TimeoutError:
                    yield ": ping\n\n"
        finally:
            if run_id_str in RUN_EVENT_QUEUES and queue in RUN_EVENT_QUEUES[run_id_str]:
                RUN_EVENT_QUEUES[run_id_str].remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/comparison-runs/{run_id}/quotes/{quote_id}/delivery-slots", tags=["Delivery Slots"])
async def get_quote_delivery_slots(run_id: UUID, quote_id: UUID, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, quote_id)
    if not quote or quote.run_id != run_id:
        raise HTTPException(status_code=404, detail="Quote not found")

    adapter_cls = ADAPTER_MAP.get(quote.retailer_id)
    if not adapter_cls:
        raise HTTPException(status_code=400, detail="Unknown retailer")
    adapter = adapter_cls()
    slots = await adapter.list_delivery_slots()
    return slots


@app.post("/comparison-runs/{run_id}/quotes/{quote_id}/select-slot", tags=["Delivery Slots"])
async def select_quote_delivery_slot(run_id: UUID, quote_id: UUID, payload: SelectSlotRequest, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, quote_id)
    if not quote or quote.run_id != run_id:
        raise HTTPException(status_code=404, detail="Quote not found")

    adapter_cls = ADAPTER_MAP.get(quote.retailer_id)
    if not adapter_cls:
        raise HTTPException(status_code=400, detail="Unknown retailer")
    adapter = adapter_cls()

    success = await adapter.select_delivery_slot(payload.slot_id)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or unavailable delivery slot")

    slots = await adapter.list_delivery_slots()
    chosen_slot = next((s for s in slots if s.slot_id == payload.slot_id), None)
    if chosen_slot:
        quote.selected_delivery_slot_id = chosen_slot.slot_id
        quote.selected_delivery_slot_window = chosen_slot.display_label
        quote.slot_fee_cents = chosen_slot.fee_cents
        fees_total = quote.delivery_fee_cents + quote.service_fee_cents + quote.bag_fee_cents + quote.slot_fee_cents
        quote.gross_total_cents = quote.subtotal_cents + fees_total
        tax_info = calculate_gst_inclusive(quote.gross_total_cents)
        quote.derived_net_cents = tax_info["net_cents"]
        quote.gst_cents = tax_info["gst_cents"]

        lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == quote.id)).all()
        line_dicts = [
            {
                "shopping_item_id": line_item.shopping_item_id,
                "retailer_sku": line_item.retailer_sku,
                "requested_quantity": line_item.requested_quantity,
                "unit_price_cents": line_item.unit_price_cents,
                "line_total_cents": line_item.line_total_cents,
            }
            for line_item in lines
        ]
        quote.cart_fingerprint = compute_quote_fingerprint(
            retailer_id=quote.retailer_id,
            lines=line_dicts,
            delivery_slot_id=quote.selected_delivery_slot_id,
            subtotal_cents=quote.subtotal_cents,
            fees_total_cents=fees_total,
            gross_total_cents=quote.gross_total_cents,
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)

    return quote


# -----------------------------------------------------------------------------
# Approval & Order Placement Flow
# -----------------------------------------------------------------------------
@app.post("/quotes/{quote_id}/approve", response_model=dict[str, Any], status_code=status.HTTP_200_OK, tags=["Ordering"])
def approve_quote_direct(quote_id: UUID, payload: QuoteApproveRequest, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if not quote.is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN",
                "message": f"Cannot approve quote with {quote.missing_must_have_count} missing must-have items.",
            },
        )

    now = datetime.now(UTC)
    if ensure_utc(quote.expires_at) < now:
        raise HTTPException(status_code=400, detail="Quote has expired")

    token = f"appr_{uuid4().hex}"
    idempotency = payload.idempotency_key or f"idem_{uuid4().hex}"

    approval = Approval(
        quote_id=quote.id,
        approval_token=token,
        idempotency_key=idempotency,
        delivery_slot_id=payload.delivery_slot_id,
        expected_fingerprint=quote.cart_fingerprint,
        is_used=False,
        approved_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    return {
        "approval_id": approval.id,
        "approval_token": approval.approval_token,
        "expires_at": approval.expires_at.isoformat(),
        "store_id": quote.retailer_id,
        "gross_total_cents": quote.gross_total_cents,
        "delivery_slot_id": approval.delivery_slot_id,
    }


@app.post("/approvals", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED, tags=["Ordering"])
def create_approval(payload: ApprovalCreate, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, payload.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if not quote.is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "INCOMPLETE_QUOTE_APPROVAL_FORBIDDEN",
                "message": f"Cannot approve quote with {quote.missing_must_have_count} missing must-have items.",
            },
        )

    now = datetime.now(UTC)
    if ensure_utc(quote.expires_at) < now:
        raise HTTPException(status_code=400, detail="Quote has expired")

    token = f"appr_{uuid4().hex}"
    idempotency = payload.idempotency_key or f"idem_{uuid4().hex}"

    approval = Approval(
        quote_id=quote.id,
        approval_token=token,
        idempotency_key=idempotency,
        delivery_slot_id=payload.delivery_slot_id,
        expected_fingerprint=quote.cart_fingerprint,
        is_used=False,
        approved_at=now,
        expires_at=now + timedelta(minutes=15),
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    return {
        "approval_id": approval.id,
        "approval_token": approval.approval_token,
        "expires_at": approval.expires_at.isoformat(),
        "store_id": quote.retailer_id,
        "gross_total_cents": quote.gross_total_cents,
        "delivery_slot_id": approval.delivery_slot_id,
    }


@app.post("/approvals/{approval_id}/submit", tags=["Ordering"])
async def submit_order_approval(approval_id: UUID, request: Request, session: Session = Depends(get_session)):
    # Strict Client Boundary Check: Reject any client-authoritative prices or line payloads
    body = await request.json()
    forbidden_keys = {"price", "prices", "total", "items", "cart_lines", "subtotal", "gst"}
    if any(k in body for k in forbidden_keys):
        raise HTTPException(status_code=400, detail="Client-authoritative pricing or item tampering rejected")

    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.is_used:
        raise HTTPException(status_code=409, detail="Approval token has already been used")

    now = datetime.now(UTC)
    if ensure_utc(approval.expires_at) < now:
        raise HTTPException(status_code=400, detail="Approval token has expired")

    provided_token = body.get("approval_token")
    if not provided_token or provided_token != approval.approval_token:
        raise HTTPException(status_code=403, detail="Invalid approval token")

    quote = session.get(StoreQuote, approval.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Store quote not found")

    # Finding #5: Fingerprint integrity check before any order action
    if quote.cart_fingerprint != approval.expected_fingerprint:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "FINGERPRINT_MISMATCH",
                "message": "Cart fingerprint has changed since approval was created. Reapproval required.",
            },
        )

    # Authoritative Pre-Checkout Revalidation
    adapter_cls = ADAPTER_MAP.get(quote.retailer_id)
    if not adapter_cls:
        raise HTTPException(status_code=400, detail="Retailer adapter not found")
    adapter = adapter_cls()

    diff = await adapter.revalidate_cart(quote)
    if diff.has_changes:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "REAPPROVAL_REQUIRED",
                "message": diff.detail or "Cart price or availability changed",
                "diff": diff.model_dump(),
            },
        )

    # Finding #3: Live checkout is not yet implemented — return 503 before any order is placed.
    # This guard is unconditional: submit_order() raises NotImplementedError in all adapters.
    # LIVE_PURCHASE_ENABLED check is removed; re-enable only when real browser checkout is wired.
    try:
        try:
            confirmation = await adapter.submit_order(approval.approval_token, approval.delivery_slot_id)
        except TypeError:
            confirmation = await adapter.submit_order(approval.approval_token)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "LIVE_CHECKOUT_NOT_IMPLEMENTED",
                "message": str(exc),
            },
        ) from exc

    # Only reached once real browser checkout is wired and submit_order returns a genuine confirmation.
    receipt = OrderReceipt(
        approval_id=approval.id,
        retailer_order_id=confirmation.retailer_order_id,
        retailer_id=quote.retailer_id,
        confirmed_total_cents=confirmation.confirmed_total_cents,
        confirmed_delivery_slot=confirmation.delivery_slot,
        receipt_url=confirmation.receipt_url,
        placed_at=confirmation.placed_at,
    )
    approval.is_used = True
    session.add(approval)
    session.add(receipt)
    session.commit()
    session.refresh(receipt)

    return {
        "status": "CONFIRMED",
        "order_id": receipt.id,
        "receipt_id": receipt.id,
        "retailer_order_id": receipt.retailer_order_id,
        "retailer_id": receipt.retailer_id,
        "confirmed_total_cents": receipt.confirmed_total_cents,
        "delivery_slot": receipt.confirmed_delivery_slot,
        "receipt_url": receipt.receipt_url,
        "placed_at": receipt.placed_at.isoformat(),
    }


@app.get("/orders/{order_id}", tags=["Ordering"])
def get_order_receipt(order_id: UUID, session: Session = Depends(get_session)):
    receipt = session.get(OrderReceipt, order_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Order receipt not found")
    return {
        "id": receipt.id,
        "order_id": receipt.id,
        "retailer_order_id": receipt.retailer_order_id,
        "retailer_id": receipt.retailer_id,
        "confirmed_total_cents": receipt.confirmed_total_cents,
        "delivery_slot": receipt.confirmed_delivery_slot,
        "receipt_url": receipt.receipt_url,
        "placed_at": receipt.placed_at.isoformat(),
    }
