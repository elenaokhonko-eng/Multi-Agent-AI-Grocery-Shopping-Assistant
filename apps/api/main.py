import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine, select

from domain.models.core import (
    Approval,
    ComparisonRun,
    ComparisonSnapshot,
    OrderReceipt,
    QuoteLine,
    ShoppingList,
    ShoppingListItem,
    StoreQuote,
    SubstitutionPolicy,
    UserProductCorrection,
)
from domain.services.fingerprint import compute_quote_fingerprint
from domain.services.pricing import calculate_gst_inclusive
from orchestration.state_machine import StateMachine, StoreState, StoreStateEvent

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
        return dt.replace(tzinfo=timezone.utc)
    return dt


# In-memory SSE event bus per comparison run
RUN_EVENT_QUEUES: Dict[str, List[asyncio.Queue]] = {}


def broadcast_run_event(run_id: str, event: StoreStateEvent):
    queues = RUN_EVENT_QUEUES.get(run_id, [])
    for q in queues:
        q.put_nowait(event)


# -----------------------------------------------------------------------------
# Lifespan / Startup Handler
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # For SQLite local dev/tests, initialize schema if not present
    if DATABASE_URL.startswith("sqlite"):
        SQLModel.metadata.create_all(engine)
    
    # Auto-seed default canonical shopping list if empty
    with Session(engine) as session:
        existing = session.exec(select(ShoppingList)).first()
        if not existing:
            default_list = ShoppingList(
                name="Weekly Family Groceries",
                description="Elena's regular grocery basket for Singapore supermarkets"
            )
            session.add(default_list)
            session.commit()
            session.refresh(default_list)

            items_data = [
                {"name": "Meiji Fresh Milk 2L", "category": "Dairy", "desired_quantity": 2, "unit_measure": "L", "must_have": True, "preferred_brands": ["Meiji"], "pinned_skus": {"fairprice": "FP_102030", "shengsiong": "SS_203040"}},
                {"name": "Fresh Eggs 10s", "category": "Eggs", "desired_quantity": 1, "unit_measure": "pack", "must_have": True, "preferred_brands": ["Dasoon", "Chew's"], "pinned_skus": {"fairprice": "FP_112233"}},
                {"name": "Fresh Lemons", "category": "Produce", "desired_quantity": 3, "unit_measure": "pieces", "must_have": True, "exclusions": ["detergent", "tea", "toiletries", "cleaning"]},
                {"name": "San Pellegrino Sparkling Water 1L", "category": "Beverages", "desired_quantity": 4, "unit_measure": "L", "must_have": False, "preferred_brands": ["San Pellegrino"]},
            ]
            for item in items_data:
                db_item = ShoppingListItem(
                    shopping_list_id=default_list.id,
                    name=item["name"],
                    category=item.get("category"),
                    desired_quantity=item["desired_quantity"],
                    unit_measure=item["unit_measure"],
                    must_have=item["must_have"],
                    preferred_brands=item.get("preferred_brands", []),
                    exclusions=item.get("exclusions", []),
                    pinned_skus=item.get("pinned_skus", {}),
                )
                session.add(db_item)
            session.commit()
    yield


app = FastAPI(
    title="Singapore Grocery Shopping Assistant API",
    version="1.0.0",
    description="Unified control plane for multi-agent grocery shopping orchestration.",
    lifespan=lifespan,
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# DTO Schemas
# -----------------------------------------------------------------------------
class ShoppingListCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ShoppingListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ShoppingListItemCreate(BaseModel):
    name: str
    category: Optional[str] = None
    desired_quantity: int = 1
    unit_measure: str = "pack"
    min_pack_size: Optional[str] = None
    max_pack_size: Optional[str] = None
    must_have: bool = True
    is_enabled: bool = True
    substitution_policy: SubstitutionPolicy = SubstitutionPolicy.SAME_BRAND_ONLY
    preferred_brands: List[str] = []
    exclusions: List[str] = []
    pinned_skus: Dict[str, str] = {}


class ShoppingListItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    desired_quantity: Optional[int] = None
    unit_measure: Optional[str] = None
    min_pack_size: Optional[str] = None
    max_pack_size: Optional[str] = None
    must_have: Optional[bool] = None
    is_enabled: Optional[bool] = None
    substitution_policy: Optional[SubstitutionPolicy] = None
    preferred_brands: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    pinned_skus: Optional[Dict[str, str]] = None


class ComparisonRunCreate(BaseModel):
    shopping_list_id: UUID
    retailer_ids: List[str] = ["fairprice", "shengsiong", "littlefarms", "redmart"]


class QuoteApproveRequest(BaseModel):
    delivery_slot_id: str


class ApprovalSubmitRequest(BaseModel):
    approval_token: str


# -----------------------------------------------------------------------------
# Health & Status
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Singapore Grocery Shopping Assistant API",
        "version": "1.0.0",
        "live_purchase_enabled": os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true",
    }


# -----------------------------------------------------------------------------
# Shopping List Endpoints (GE-02, GE-03)
# -----------------------------------------------------------------------------
@app.get("/shopping-lists")
def list_shopping_lists(session: Session = Depends(get_session)):
    lists = session.exec(select(ShoppingList).where(ShoppingList.is_active == True)).all()
    result = []
    for l in lists:
        result.append({
            "id": str(l.id),
            "name": l.name,
            "description": l.description,
            "version": l.version,
            "is_active": l.is_active,
            "created_at": l.created_at.isoformat(),
            "updated_at": l.updated_at.isoformat(),
            "items_count": len(l.items)
        })
    return result


@app.post("/shopping-lists", status_code=status.HTTP_201_CREATED)
def create_shopping_list(payload: ShoppingListCreate, session: Session = Depends(get_session)):
    new_list = ShoppingList(name=payload.name, description=payload.description)
    session.add(new_list)
    session.commit()
    session.refresh(new_list)
    return new_list


@app.get("/shopping-lists/{list_id}")
def get_shopping_list(list_id: UUID, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    items = session.exec(select(ShoppingListItem).where(ShoppingListItem.shopping_list_id == list_id)).all()
    return {
        "id": str(s_list.id),
        "name": s_list.name,
        "description": s_list.description,
        "version": s_list.version,
        "is_active": s_list.is_active,
        "created_at": s_list.created_at.isoformat(),
        "updated_at": s_list.updated_at.isoformat(),
        "items": [
            {
                "id": str(item.id),
                "name": item.name,
                "category": item.category,
                "desired_quantity": item.desired_quantity,
                "unit_measure": item.unit_measure,
                "must_have": item.must_have,
                "is_enabled": item.is_enabled,
                "substitution_policy": item.substitution_policy,
                "preferred_brands": item.preferred_brands or [],
                "exclusions": item.exclusions or [],
                "pinned_skus": item.pinned_skus or {},
            }
            for item in items
        ]
    }


@app.patch("/shopping-lists/{list_id}")
def update_shopping_list(list_id: UUID, payload: ShoppingListUpdate, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    if payload.name is not None:
        s_list.name = payload.name
    if payload.description is not None:
        s_list.description = payload.description
    if payload.is_active is not None:
        s_list.is_active = payload.is_active
    
    s_list.version += 1
    s_list.updated_at = datetime.now(timezone.utc)
    session.add(s_list)
    session.commit()
    session.refresh(s_list)
    return s_list


@app.post("/shopping-lists/{list_id}/items", status_code=status.HTTP_201_CREATED)
def add_item_to_shopping_list(list_id: UUID, payload: ShoppingListItemCreate, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    new_item = ShoppingListItem(
        shopping_list_id=list_id,
        name=payload.name,
        category=payload.category,
        desired_quantity=payload.desired_quantity,
        unit_measure=payload.unit_measure,
        min_pack_size=payload.min_pack_size,
        max_pack_size=payload.max_pack_size,
        must_have=payload.must_have,
        is_enabled=payload.is_enabled,
        substitution_policy=payload.substitution_policy,
        preferred_brands=payload.preferred_brands,
        exclusions=payload.exclusions,
        pinned_skus=payload.pinned_skus,
    )
    session.add(new_item)
    s_list.version += 1
    s_list.updated_at = datetime.now(timezone.utc)
    session.add(s_list)
    session.commit()
    session.refresh(new_item)
    return new_item


@app.patch("/shopping-lists/{list_id}/items/{item_id}")
def update_shopping_list_item(list_id: UUID, item_id: UUID, payload: ShoppingListItemUpdate, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=404, detail="Item not found on shopping list")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, val)

    item.updated_at = datetime.now(timezone.utc)
    session.add(item)
    s_list.version += 1
    s_list.updated_at = datetime.now(timezone.utc)
    session.add(s_list)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/shopping-lists/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shopping_list_item(list_id: UUID, item_id: UUID, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    item = session.get(ShoppingListItem, item_id)
    if not item or item.shopping_list_id != list_id:
        raise HTTPException(status_code=404, detail="Item not found on shopping list")

    session.delete(item)
    s_list.version += 1
    s_list.updated_at = datetime.now(timezone.utc)
    session.add(s_list)
    session.commit()
    return None


# -----------------------------------------------------------------------------
# Comparison Runs & Orchestration (GE-04, GE-06)
# -----------------------------------------------------------------------------
async def execute_mock_retailer_worker(run_id: str, retailer_id: str, items: List[Dict[str, Any]], session_factory):
    sm = StateMachine(run_id=run_id, retailer_id=retailer_id, event_callback=lambda evt: broadcast_run_event(run_id, evt))
    
    # 1. Session Check
    await sm.transition(StoreState.SESSION_CHECK, progress_pct=15, detail="Validating store session")
    await asyncio.sleep(0.3)
    
    # 2. Searching
    await sm.transition(StoreState.SEARCHING, progress_pct=40, detail=f"Searching catalog for {len(items)} items")
    await asyncio.sleep(0.4)
    
    # 3. Matching
    await sm.transition(StoreState.MATCHING, progress_pct=65, detail="Applying brand & pack filters")
    await asyncio.sleep(0.3)
    
    # 4. Cart Preparing & Reading
    await sm.transition(StoreState.CART_PREPARING, progress_pct=85, detail="Building store basket")
    await asyncio.sleep(0.3)
    await sm.transition(StoreState.CART_READING, progress_pct=95, detail="Reading authoritative lines & fees")
    
    # Build Store Quote
    with session_factory() as session:
        quote_lines_payload = []
        subtotal_cents = 0
        all_must_have_found = True
        
        # Price table simulation per store
        store_multiplier = {"fairprice": 1.0, "shengsiong": 0.94, "littlefarms": 1.35, "redmart": 1.02}.get(retailer_id, 1.0)
        
        for idx, item in enumerate(items):
            base_unit_price = 450 + (idx * 150)
            item_price = int(base_unit_price * store_multiplier)
            qty = item.get("desired_quantity", 1)
            line_total = item_price * qty
            subtotal_cents += line_total
            
            quote_lines_payload.append({
                "shopping_item_id": UUID(item["id"]) if isinstance(item["id"], str) else item["id"],
                "retailer_sku": item.get("pinned_skus", {}).get(retailer_id, f"{retailer_id.upper()}_{idx+1000}"),
                "product_title": f"{item['name']} ({retailer_id.capitalize()})",
                "product_brand": item.get("preferred_brands", ["StoreBrand"])[0] if item.get("preferred_brands") else "Generic",
                "product_url": f"https://www.{retailer_id}.com.sg/p/{idx+1000}",
                "image_url": f"https://images.{retailer_id}.com.sg/{idx+1000}.jpg",
                "pack_size": "Standard",
                "requested_quantity": qty,
                "packs_added": qty,
                "is_in_stock": True,
                "is_exact_match": True,
                "is_substituted": False,
                "missing_reason": None,
                "unit_price_cents": item_price,
                "unit_measure": item.get("unit_measure", "pack"),
                "line_total_cents": line_total
            })

        delivery_fee = 0 if subtotal_cents >= 7900 else 550
        service_fee = 0
        bag_fee = 20
        slot_fee = 0
        fees_total = delivery_fee + service_fee + bag_fee + slot_fee
        gross_total = subtotal_cents + fees_total
        
        tax_info = calculate_gst_inclusive(gross_total)
        default_slot_id = f"slot_{retailer_id}_tomorrow_am"
        
        fingerprint = compute_quote_fingerprint(
            retailer_id=retailer_id,
            lines=quote_lines_payload,
            delivery_slot_id=default_slot_id,
            subtotal_cents=subtotal_cents,
            fees_total_cents=fees_total,
            gross_total_cents=gross_total
        )
        
        db_quote = StoreQuote(
            run_id=UUID(run_id),
            retailer_id=retailer_id,
            retailer_cart_id=f"cart_{retailer_id}_{uuid4().hex[:6]}",
            cart_url=f"https://www.{retailer_id}.com.sg/cart",
            cart_fingerprint=fingerprint,
            subtotal_cents=subtotal_cents,
            promotions_discount_cents=0,
            delivery_fee_cents=delivery_fee,
            service_fee_cents=service_fee,
            bag_fee_cents=bag_fee,
            slot_fee_cents=slot_fee,
            gross_total_cents=gross_total,
            derived_net_cents=tax_info["net_cents"],
            gst_cents=tax_info["gst_cents"],
            free_delivery_threshold_cents=7900,
            amount_needed_for_free_delivery_cents=max(0, 7900 - subtotal_cents),
            is_complete=all_must_have_found,
            missing_must_have_count=0,
            selected_delivery_slot_id=default_slot_id,
            selected_delivery_slot_window="Tomorrow 09:00 - 11:00",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
        )
        session.add(db_quote)
        session.commit()
        session.refresh(db_quote)
        
        for ql in quote_lines_payload:
            db_line = QuoteLine(
                quote_id=db_quote.id,
                **ql
            )
            session.add(db_line)
        session.commit()
        
        await sm.transition(
            StoreState.QUOTED,
            progress_pct=100,
            detail=f"Quote ready: S${gross_total/100:.2f}",
            quote_id=str(db_quote.id)
        )


@app.post("/comparison-runs", status_code=status.HTTP_202_ACCEPTED)
async def create_comparison_run(payload: ComparisonRunCreate, session: Session = Depends(get_session)):
    s_list = session.get(ShoppingList, payload.shopping_list_id)
    if not s_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    items = session.exec(select(ShoppingListItem).where(
        ShoppingListItem.shopping_list_id == payload.shopping_list_id,
        ShoppingListItem.is_enabled == True
    )).all()
    
    if not items:
        raise HTTPException(status_code=400, detail="Shopping list has no enabled items")

    # Create immutable ComparisonSnapshot (GE-03)
    frozen_items = [
        {
            "id": str(item.id),
            "name": item.name,
            "category": item.category,
            "desired_quantity": item.desired_quantity,
            "unit_measure": item.unit_measure,
            "must_have": item.must_have,
            "preferred_brands": item.preferred_brands or [],
            "exclusions": item.exclusions or [],
            "pinned_skus": item.pinned_skus or {},
        }
        for item in items
    ]
    snapshot = ComparisonSnapshot(
        shopping_list_id=s_list.id,
        list_version=s_list.version,
        frozen_items_json=frozen_items
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    # Initialize ComparisonRun
    run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
    session.add(run)
    session.commit()
    session.refresh(run)

    run_id_str = str(run.id)
    RUN_EVENT_QUEUES[run_id_str] = []

    # Launch background concurrent retailer workers
    for ret_id in payload.retailer_ids:
        asyncio.create_task(execute_mock_retailer_worker(run_id_str, ret_id, frozen_items, lambda: Session(engine)))

    return {
        "run_id": run_id_str,
        "snapshot_id": str(snapshot.id),
        "status": "QUEUED",
        "retailers": payload.retailer_ids,
        "items_count": len(items),
        "created_at": run.created_at.isoformat()
    }


@app.get("/comparison-runs/{run_id}")
def get_comparison_run(run_id: UUID, session: Session = Depends(get_session)):
    run = session.get(ComparisonRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Comparison run not found")

    quotes = session.exec(select(StoreQuote).where(StoreQuote.run_id == run_id)).all()
    quotes_data = []
    cheapest_complete = None
    min_total = float("inf")

    for q in quotes:
        lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == q.id)).all()
        q_dict = {
            "quote_id": str(q.id),
            "retailer_id": q.retailer_id,
            "cart_fingerprint": q.cart_fingerprint,
            "subtotal_cents": q.subtotal_cents,
            "delivery_fee_cents": q.delivery_fee_cents,
            "service_fee_cents": q.service_fee_cents,
            "gross_total_cents": q.gross_total_cents,
            "derived_net_cents": q.derived_net_cents,
            "gst_cents": q.gst_cents,
            "is_complete": q.is_complete,
            "selected_delivery_slot_id": q.selected_delivery_slot_id,
            "selected_delivery_slot_window": q.selected_delivery_slot_window,
            "expires_at": q.expires_at.isoformat(),
            "lines": [
                {
                    "shopping_item_id": str(l.shopping_item_id),
                    "retailer_sku": l.retailer_sku,
                    "product_title": l.product_title,
                    "product_brand": l.product_brand,
                    "unit_price_cents": l.unit_price_cents,
                    "packs_added": l.packs_added,
                    "line_total_cents": l.line_total_cents,
                    "is_in_stock": l.is_in_stock,
                    "is_exact_match": l.is_exact_match,
                }
                for l in lines
            ]
        }
        quotes_data.append(q_dict)
        if q.is_complete and q.gross_total_cents < min_total:
            min_total = q.gross_total_cents
            cheapest_complete = q.retailer_id

    return {
        "run_id": str(run.id),
        "status": run.status,
        "cheapest_complete_store": cheapest_complete,
        "quotes": quotes_data
    }


@app.get("/comparison-runs/{run_id}/events")
async def stream_run_events(run_id: str, request: Request):
    q: asyncio.Queue = asyncio.Queue()
    if run_id not in RUN_EVENT_QUEUES:
        RUN_EVENT_QUEUES[run_id] = []
    RUN_EVENT_QUEUES[run_id].append(q)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event: StoreStateEvent = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield f"event: store_state\ndata: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError:
                    yield f": ping {datetime.now(timezone.utc).isoformat()}\n\n"
        finally:
            if run_id in RUN_EVENT_QUEUES and q in RUN_EVENT_QUEUES[run_id]:
                RUN_EVENT_QUEUES[run_id].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# -----------------------------------------------------------------------------
# Approvals & Order Submission (GE-07, GE-08)
# -----------------------------------------------------------------------------
@app.post("/quotes/{quote_id}/approve")
def approve_quote(quote_id: UUID, payload: QuoteApproveRequest, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if ensure_utc(quote.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Quote has expired")

    token = f"tok_{uuid4().hex}"
    idempotency = f"idem_{uuid4().hex}"
    approval = Approval(
        quote_id=quote.id,
        approval_token=token,
        idempotency_key=idempotency,
        delivery_slot_id=payload.delivery_slot_id,
        expected_fingerprint=quote.cart_fingerprint,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)

    return {
        "approval_id": str(approval.id),
        "approval_token": approval.approval_token,
        "quote_id": str(quote.id),
        "retailer_id": quote.retailer_id,
        "gross_total_cents": quote.gross_total_cents,
        "delivery_slot_id": approval.delivery_slot_id,
        "expires_at": approval.expires_at.isoformat()
    }


@app.post("/approvals/{approval_id}/submit")
def submit_approval(approval_id: UUID, payload: ApprovalSubmitRequest, session: Session = Depends(get_session)):
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.approval_token != payload.approval_token:
        raise HTTPException(status_code=403, detail="Invalid approval token")

    if approval.is_used:
        raise HTTPException(status_code=409, detail="Approval token has already been used")

    if ensure_utc(approval.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Approval token has expired")

    quote = session.get(StoreQuote, approval.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Underlying quote not found")

    # Safety Guard (GE-08)
    live_enabled = os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
    if not live_enabled:
        raise HTTPException(
            status_code=403,
            detail="LIVE_PURCHASE_DISABLED: Live transactions are disabled until architectural release sign-off."
        )

    # In live mode, simulate deterministic order confirmation
    approval.is_used = True
    session.add(approval)

    retailer_order_num = f"{quote.retailer_id.upper()}-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    receipt = OrderReceipt(
        approval_id=approval.id,
        retailer_order_id=retailer_order_num,
        retailer_id=quote.retailer_id,
        confirmed_total_cents=quote.gross_total_cents,
        confirmed_delivery_slot=quote.selected_delivery_slot_window or "Default Slot",
        receipt_url=f"https://www.{quote.retailer_id}.com.sg/receipts/{retailer_order_num}"
    )
    session.add(receipt)
    session.commit()
    session.refresh(receipt)

    return {
        "order_id": str(receipt.id),
        "retailer_order_id": receipt.retailer_order_id,
        "retailer_id": receipt.retailer_id,
        "confirmed_total_cents": receipt.confirmed_total_cents,
        "confirmed_delivery_slot": receipt.confirmed_delivery_slot,
        "receipt_url": receipt.receipt_url,
        "status": "CONFIRMED",
        "placed_at": receipt.placed_at.isoformat()
    }


@app.get("/orders/{order_id}")
def get_order(order_id: UUID, session: Session = Depends(get_session)):
    receipt = session.get(OrderReceipt, order_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Order receipt not found")
    return {
        "order_id": str(receipt.id),
        "retailer_order_id": receipt.retailer_order_id,
        "retailer_id": receipt.retailer_id,
        "confirmed_total_cents": receipt.confirmed_total_cents,
        "confirmed_delivery_slot": receipt.confirmed_delivery_slot,
        "receipt_url": receipt.receipt_url,
        "placed_at": receipt.placed_at.isoformat()
    }
