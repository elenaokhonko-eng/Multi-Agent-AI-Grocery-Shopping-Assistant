import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from domain.models.core import (
    ComparisonRun,
    ComparisonSnapshot,
    QuoteLine,
    QuoteRevision,
    ShoppingList,
    ShoppingListItem,
    StoreEventLog,
    StoreQuote,
)
from domain.services.fingerprint import compute_quote_fingerprint
from domain.services.matching import match_product_candidate
from domain.services.pricing import calculate_gst_inclusive
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from orchestration.state_machine import StateMachine, StoreState, StoreStateEvent
from orchestration.task_queue import DurableTaskQueue
from sqlmodel import Session, select

from apps.api.core import (
    ADAPTER_MAP,
    RUN_EVENT_QUEUES,
    broadcast_run_event,
    get_session,
)
from apps.api.schemas import (
    ComparisonRunCreate,
    SelectSlotRequest,
    StoreEventResponse,
    StoreQuoteRead,
)
from packages.retailers.base import RetailerAdapter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Comparison Runs & Quotes"])


async def run_retailer_worker(
    run_id: str,
    retailer_id: str,
    frozen_items: list[dict[str, Any]],
    session_factory,
    adapter_override: RetailerAdapter | None = None,
):
    sm = StateMachine(run_id=run_id, retailer_id=retailer_id)
    worker_id = f"worker_{uuid.uuid4().hex[:8]}"
    claimed_task_id: UUID | None = None

    try:
        with session_factory() as s:
            t = DurableTaskQueue.claim_task(s, worker_id=worker_id, retailer_id=retailer_id)
            if t:
                claimed_task_id = t.id
    except Exception as e:
        logger.debug("Task claim error: %s", e)

    if adapter_override:
        adapter = adapter_override
    else:
        adapter_cls = ADAPTER_MAP.get(retailer_id)
        if not adapter_cls:
            evt = await sm.transition(StoreState.FAILED, detail=f"Unsupported retailer: {retailer_id}")
            broadcast_run_event(run_id, evt)
            if claimed_task_id:
                try:
                    with session_factory() as s:
                        DurableTaskQueue.fail_task(
                            s, claimed_task_id, worker_id, f"Unsupported retailer: {retailer_id}"
                        )
                        DurableTaskQueue.aggregate_run_state(s, UUID(run_id))
                except Exception:
                    pass
            return
        adapter = adapter_cls()

    try:
        evt = await sm.transition(StoreState.SESSION_CHECK, detail="Checking browser session")
        broadcast_run_event(run_id, evt)
        await asyncio.sleep(0.05)

        sess_status = await adapter.check_session()
        is_auth = getattr(sess_status, "is_authenticated", False)
        auth_detail = getattr(sess_status, "auth_error", None) or getattr(sess_status, "user_name", None)

        if not is_auth:
            evt = await sm.transition(
                StoreState.USER_ACTION_REQUIRED,
                detail=auth_detail or "Authentication or challenge resolution required",
                challenge_type="LOGIN_REQUIRED",
                resume_token=f"tok_{retailer_id}_{run_id[:8]}",
            )
            broadcast_run_event(run_id, evt)
            if claimed_task_id:
                try:
                    with session_factory() as s:
                        DurableTaskQueue.set_task_action_required(
                            s, claimed_task_id, worker_id, auth_detail or "Authentication required"
                        )
                        DurableTaskQueue.aggregate_run_state(s, UUID(run_id))
                except Exception:
                    pass
            return

        # Pre-mutation cart check (AD-09: pre-mutation unowned cart protection)
        read_cart_fn = getattr(adapter, "read_cart", getattr(adapter, "read_authoritative_cart", None))
        if read_cart_fn:
            try:
                pre_cart = await read_cart_fn()
                if pre_cart and getattr(pre_cart, "unowned_items_detected", False):
                    evt = await sm.transition(
                        StoreState.USER_ACTION_REQUIRED,
                        detail=f"Pre-existing unowned items found in {retailer_id} cart. Never clear without user permission.",
                        challenge_type="CART_CONFLICT",
                        resume_token=f"tok_cart_conflict_{retailer_id}_{run_id[:8]}",
                    )
                    broadcast_run_event(run_id, evt)
                    if claimed_task_id:
                        try:
                            with session_factory() as s:
                                DurableTaskQueue.set_task_action_required(
                                    s, claimed_task_id, worker_id, "Pre-existing unowned items in cart"
                                )
                                DurableTaskQueue.aggregate_run_state(s, UUID(run_id))
                        except Exception:
                            pass
                    return
            except Exception as e:
                logger.debug("Pre-cart check skipped: %s", e)

        evt = await sm.transition(StoreState.SEARCHING, detail="Searching product catalog", progress_pct=20)
        broadcast_run_event(run_id, evt)

        quote_lines: list[dict[str, Any]] = []
        subtotal_cents = 0
        missing_must_have = 0
        missing_total = 0
        found_total = 0
        total_items = len(frozen_items)

        for idx, item in enumerate(frozen_items):
            if not item.get("is_enabled", True):
                continue

            item_name = item.get("name", "")
            pinned_skus = item.get("pinned_skus") or {}
            pinned_sku = pinned_skus.get(retailer_id)

            candidates = await adapter.search_candidates(
                query=item_name,
                category_hint=item.get("category"),
            )

            matched_candidate = None
            packs_to_add = 1
            missing_reason = None

            if pinned_sku:
                for cand in candidates:
                    cand_sku = getattr(cand, "retailer_sku", getattr(cand, "sku", ""))
                    if cand_sku == pinned_sku:
                        cand_title = getattr(cand, "title", "")
                        cand_brand = getattr(cand, "brand", None)
                        cand_cat = getattr(cand, "category", None)
                        cand_pack = getattr(cand, "pack_size", None)
                        is_match, packs, rej = match_product_candidate(
                            cand_title, cand_sku, cand_brand, cand_cat, cand_pack, item
                        )
                        if is_match:
                            matched_candidate = cand
                            packs_to_add = packs
                            break

            if not matched_candidate:
                for cand in candidates:
                    cand_sku = getattr(cand, "retailer_sku", getattr(cand, "sku", ""))
                    cand_title = getattr(cand, "title", "")
                    cand_brand = getattr(cand, "brand", None)
                    cand_cat = getattr(cand, "category", None)
                    cand_pack = getattr(cand, "pack_size", None)
                    is_match, packs, rej = match_product_candidate(
                        cand_title, cand_sku, cand_brand, cand_cat, cand_pack, item
                    )
                    if is_match:
                        matched_candidate = cand
                        packs_to_add = packs
                        break
                    else:
                        missing_reason = rej

            if matched_candidate:
                cand_sku = getattr(matched_candidate, "retailer_sku", getattr(matched_candidate, "sku", ""))
                cand_price = getattr(
                    matched_candidate, "price_cents", getattr(matched_candidate, "unit_price_cents", 0)
                )
                cand_title = getattr(matched_candidate, "title", "")
                cand_brand = getattr(matched_candidate, "brand", None)
                cand_url = getattr(matched_candidate, "product_url", "")
                cand_img = getattr(matched_candidate, "image_url", None)
                cand_pack = getattr(matched_candidate, "pack_size", None)

                add_fn = getattr(adapter, "add_item_to_cart", getattr(adapter, "add_to_cart", None))
                added = await add_fn(cand_sku, packs_to_add) if add_fn else True

                if added:
                    found_total += 1
                    line_total = cand_price * packs_to_add
                    subtotal_cents += line_total
                    quote_lines.append(
                        {
                            "shopping_item_id": item["id"],
                            "retailer_sku": cand_sku,
                            "product_title": cand_title,
                            "product_brand": cand_brand,
                            "product_url": cand_url,
                            "image_url": cand_img,
                            "pack_size": cand_pack,
                            "requested_quantity": item.get("desired_quantity", 1),
                            "packs_added": packs_to_add,
                            "is_in_stock": True,
                            "is_exact_match": True,
                            "is_substituted": False,
                            "missing_reason": None,
                            "unit_price_cents": cand_price,
                            "unit_measure": item.get("unit_measure", "pack"),
                            "line_total_cents": line_total,
                        }
                    )
                else:
                    missing_total += 1
                    if item.get("must_have", True):
                        missing_must_have += 1
                    quote_lines.append(
                        {
                            "shopping_item_id": item["id"],
                            "retailer_sku": cand_sku,
                            "product_title": cand_title,
                            "product_brand": cand_brand,
                            "product_url": cand_url,
                            "image_url": cand_img,
                            "pack_size": cand_pack,
                            "requested_quantity": item.get("desired_quantity", 1),
                            "packs_added": 0,
                            "is_in_stock": False,
                            "is_exact_match": False,
                            "is_substituted": False,
                            "missing_reason": "Out of stock / cart addition failed",
                            "unit_price_cents": cand_price,
                            "unit_measure": item.get("unit_measure", "pack"),
                            "line_total_cents": 0,
                        }
                    )
            else:
                missing_total += 1
                if item.get("must_have", True):
                    missing_must_have += 1
                quote_lines.append(
                    {
                        "shopping_item_id": item["id"],
                        "retailer_sku": "NOT_FOUND",
                        "product_title": item_name,
                        "product_brand": None,
                        "product_url": "",
                        "image_url": None,
                        "pack_size": None,
                        "requested_quantity": item.get("desired_quantity", 1),
                        "packs_added": 0,
                        "is_in_stock": False,
                        "is_exact_match": False,
                        "is_substituted": False,
                        "missing_reason": missing_reason or "No matching product found in catalogue",
                        "unit_price_cents": 0,
                        "unit_measure": item.get("unit_measure", "pack"),
                        "line_total_cents": 0,
                    }
                )

            progress = 20 + int((idx + 1) / total_items * 50)
            evt = await sm.transition(StoreState.CART_PREPARING, detail=f"Processed {item_name}", progress_pct=progress)
            broadcast_run_event(run_id, evt)

        evt = await sm.transition(
            StoreState.CART_READING, detail="Reading authoritative cart and slots", progress_pct=75
        )
        broadcast_run_event(run_id, evt)

        read_cart_fn = getattr(adapter, "read_cart", getattr(adapter, "read_authoritative_cart", None))
        auth_cart = await read_cart_fn() if read_cart_fn else None

        list_slots_fn = getattr(adapter, "list_delivery_slots", getattr(adapter, "get_delivery_slots", None))
        slots = await list_slots_fn() if list_slots_fn else []

        selected_slot_id = slots[0].slot_id if slots else "std_slot"
        selected_slot_window = getattr(slots[0], "display_label", None) if slots else None
        if not selected_slot_window and slots:
            selected_slot_window = f"{slots[0].start_time.strftime('%H:%M')} - {slots[0].end_time.strftime('%H:%M')}"
        if not selected_slot_window:
            selected_slot_window = "09:00 - 12:00"

        slot_fee_cents = slots[0].fee_cents if slots else 0

        if auth_cart:
            if auth_cart.subtotal_cents > 0:
                subtotal_cents = auth_cart.subtotal_cents
            del_fee = auth_cart.delivery_fee_cents
            serv_fee = auth_cart.service_fee_cents
            bag_fee = auth_cart.bag_fee_cents
            free_thresh = auth_cart.free_delivery_threshold_cents
            cart_id_val = auth_cart.cart_id or f"cart_{retailer_id}"
            if auth_cart.gross_total_cents > 0:
                gross_total = auth_cart.gross_total_cents
            else:
                gross_total = subtotal_cents + del_fee + serv_fee + bag_fee + slot_fee_cents
        else:
            del_fee = 0
            serv_fee = 0
            bag_fee = 0
            free_thresh = None
            cart_id_val = f"cart_{retailer_id}"
            gross_total = subtotal_cents + slot_fee_cents

        gst_info = calculate_gst_inclusive(subtotal_cents)
        fees_total = del_fee + serv_fee + bag_fee + slot_fee_cents

        is_all_complete = missing_total == 0
        is_req_complete = missing_must_have == 0

        raw_fingerprint_lines = [
            {
                "sku": ql["retailer_sku"],
                "quantity": ql["packs_added"],
                "unit_price_cents": ql["unit_price_cents"],
                "line_total_cents": ql["line_total_cents"],
            }
            for ql in quote_lines
            if ql["packs_added"] > 0
        ]
        fingerprint = compute_quote_fingerprint(
            retailer_id=retailer_id,
            lines=raw_fingerprint_lines,
            delivery_slot_id=selected_slot_id,
            delivery_slot_window=selected_slot_window,
            retailer_cart_id=cart_id_val,
            currency="SGD",
            promotions_discount_cents=0,
            delivery_fee_cents=del_fee,
            service_fee_cents=serv_fee,
            bag_fee_cents=bag_fee,
            slot_fee_cents=slot_fee_cents,
            subtotal_cents=subtotal_cents,
            fees_total_cents=fees_total,
            gross_total_cents=gross_total,
        )

        with session_factory() as session:
            quote = StoreQuote(
                run_id=UUID(run_id),
                retailer_id=retailer_id,
                retailer_cart_id=cart_id_val,
                cart_url=f"https://www.{retailer_id}.com.sg/cart",
                cart_fingerprint=fingerprint,
                subtotal_cents=subtotal_cents,
                promotions_discount_cents=0,
                delivery_fee_cents=del_fee,
                service_fee_cents=serv_fee,
                bag_fee_cents=bag_fee,
                slot_fee_cents=slot_fee_cents,
                gross_total_cents=gross_total,
                derived_net_cents=gst_info["net_cents"],
                gst_cents=gst_info["gst_cents"],
                free_delivery_threshold_cents=free_thresh,
                amount_needed_for_free_delivery_cents=max(0, (free_thresh or 0) - subtotal_cents),
                is_complete=is_req_complete,
                is_all_items_complete=is_all_complete,
                is_required_complete=is_req_complete,
                requested_item_count=total_items,
                found_item_count=found_total,
                missing_item_count=missing_total,
                missing_must_have_count=missing_must_have,
                missing_required_count=missing_must_have,
                selected_delivery_slot_id=selected_slot_id,
                selected_delivery_slot_window=selected_slot_window,
                expires_at=datetime.now(UTC) + timedelta(minutes=15),
            )
            session.add(quote)
            session.commit()
            session.refresh(quote)

            for ql in quote_lines:
                db_ql = QuoteLine(
                    quote_id=quote.id,
                    shopping_item_id=UUID(ql["shopping_item_id"]),
                    retailer_sku=ql["retailer_sku"],
                    product_title=ql["product_title"],
                    product_brand=ql["product_brand"],
                    product_url=ql["product_url"],
                    image_url=ql["image_url"],
                    pack_size=ql["pack_size"],
                    requested_quantity=ql["requested_quantity"],
                    packs_added=ql["packs_added"],
                    is_in_stock=ql["is_in_stock"],
                    is_exact_match=ql["is_exact_match"],
                    is_substituted=ql["is_substituted"],
                    missing_reason=ql["missing_reason"],
                    unit_price_cents=ql["unit_price_cents"],
                    unit_measure=ql["unit_measure"],
                    line_total_cents=ql["line_total_cents"],
                )
                session.add(db_ql)

            revision = QuoteRevision(
                quote_id=quote.id,
                revision_number=1,
                cart_fingerprint=quote.cart_fingerprint,
                subtotal_cents=quote.subtotal_cents,
                gross_total_cents=quote.gross_total_cents,
                selected_delivery_slot_id=quote.selected_delivery_slot_id,
            )
            session.add(revision)
            session.commit()

        terminal_state = StoreState.QUOTED if is_req_complete else StoreState.PARTIAL
        evt = await sm.transition(
            terminal_state, detail=f"Authoritative quote finalized (${gross_total / 100:.2f})", progress_pct=100
        )
        broadcast_run_event(run_id, evt)
        if claimed_task_id:
            try:
                with session_factory() as s:
                    DurableTaskQueue.complete_task(s, claimed_task_id, worker_id)
                    DurableTaskQueue.aggregate_run_state(s, UUID(run_id))
            except Exception:
                pass

    except Exception as exc:
        logger.exception("Worker failure for retailer %s on run %s", retailer_id, run_id)
        evt = await sm.transition(StoreState.FAILED, detail=str(exc), progress_pct=100)
        broadcast_run_event(run_id, evt)
        if claimed_task_id:
            try:
                with session_factory() as s:
                    DurableTaskQueue.fail_task(s, claimed_task_id, worker_id, str(exc))
                    DurableTaskQueue.aggregate_run_state(s, UUID(run_id))
            except Exception:
                pass


execute_live_retailer_worker = run_retailer_worker


@router.post("/comparison-runs", status_code=status.HTTP_202_ACCEPTED)
async def start_comparison_run(
    run_req: ComparisonRunCreate,
    session: Session = Depends(get_session),
):
    sl = session.get(ShoppingList, run_req.shopping_list_id)
    if not sl or not sl.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

    items = session.exec(
        select(ShoppingListItem)
        .where(ShoppingListItem.shopping_list_id == sl.id)
        .where(ShoppingListItem.is_enabled == True)  # noqa: E712
    ).all()

    if not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No enabled items in shopping list")

    frozen_items = [
        {
            "id": str(it.id),
            "name": it.name,
            "category": it.category,
            "desired_quantity": it.desired_quantity,
            "unit_measure": it.unit_measure,
            "min_pack_size": it.min_pack_size,
            "max_pack_size": it.max_pack_size,
            "must_have": it.must_have,
            "is_enabled": it.is_enabled,
            "substitution_policy": it.substitution_policy.value,
            "preferred_brands": it.preferred_brands,
            "exclusions": it.exclusions,
            "pinned_skus": it.pinned_skus,
        }
        for it in items
    ]

    snapshot = ComparisonSnapshot(
        shopping_list_id=sl.id,
        list_version=sl.version,
        frozen_items_json=frozen_items,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    run = ComparisonRun(snapshot_id=snapshot.id, status="QUEUED")
    session.add(run)
    session.commit()
    session.refresh(run)

    # Durable task graph enqueueing (PR-05)
    DurableTaskQueue.enqueue_run_tasks(session, run.id, run_req.target_retailers)

    run_id_str = str(run.id)
    RUN_EVENT_QUEUES[run_id_str] = []

    # Run tasks in background
    for ret_id in run_req.target_retailers:
        asyncio.create_task(
            run_retailer_worker(
                run_id=run_id_str,
                retailer_id=ret_id,
                frozen_items=frozen_items,
                session_factory=get_session,
            )
        )

    # Async run-status coordinator
    async def coordinate_run_status(r_id: str, retailers: list[str]):
        try:
            total_tasks = len(retailers)
            all_done = False
            while not all_done:
                await asyncio.sleep(0.5)
                with Session(get_session().__next__().get_bind()) as s:
                    events = s.exec(select(StoreEventLog).where(StoreEventLog.run_id == UUID(r_id))).all()
                    terminal_retailers = set()
                    has_error = False
                    for ev in events:
                        if ev.to_state in ["QUOTED", "PARTIAL", "FAILED", "BLOCKED"]:
                            terminal_retailers.add(ev.retailer_id)
                        if ev.to_state in ["FAILED", "BLOCKED"]:
                            has_error = True

                    if len(terminal_retailers) >= total_tasks:
                        all_done = True
                        db_run = s.get(ComparisonRun, UUID(r_id))
                        if db_run and db_run.status in ["QUEUED", "RUNNING"]:
                            db_run.status = "COMPLETED_WITH_ERRORS" if has_error else "COMPLETED"
                            db_run.completed_at = datetime.now(UTC)
                            s.add(db_run)
                            s.commit()
        except Exception as e:
            logger.warning("Error coordinating run status for %s: %s", r_id, e)

    asyncio.create_task(coordinate_run_status(run_id_str, run_req.target_retailers))

    return {
        "run_id": run.id,
        "snapshot_id": snapshot.id,
        "status": run.status,
        "target_retailers": run_req.target_retailers,
        "item_count": len(frozen_items),
        "created_at": run.created_at,
    }


@router.get("/comparison-runs/{run_id}")
def get_comparison_run(run_id: UUID, session: Session = Depends(get_session)):
    run = session.get(ComparisonRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison run not found")

    quotes = session.exec(select(StoreQuote).where(StoreQuote.run_id == run_id)).all()
    events = session.exec(
        select(StoreEventLog).where(StoreEventLog.run_id == run_id).order_by(StoreEventLog.created_at)
    ).all()

    quotes_data = []
    cheapest_complete_store = None
    min_gross = float("inf")
    for q in quotes:
        qd = q.model_dump()
        qd["quote_id"] = str(q.id)
        quotes_data.append(qd)
        if q.is_complete and q.gross_total_cents < min_gross:
            min_gross = q.gross_total_cents
            cheapest_complete_store = q.retailer_id

    return {
        "id": run.id,
        "run_id": run.id,
        "snapshot_id": run.snapshot_id,
        "status": run.status,
        "cheapest_complete_store": cheapest_complete_store,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "quotes": quotes_data,
        "event_logs": events,
    }


@router.get("/comparison-runs/{run_id}/events")
async def stream_comparison_events(run_id: UUID, request: Request, session: Session = Depends(get_session)):
    run = session.get(ComparisonRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison run not found")

    run_id_str = str(run_id)
    queue: asyncio.Queue = asyncio.Queue()

    # Replay historical logs first
    past_logs = session.exec(
        select(StoreEventLog).where(StoreEventLog.run_id == run_id).order_by(StoreEventLog.created_at)
    ).all()

    if run_id_str not in RUN_EVENT_QUEUES:
        RUN_EVENT_QUEUES[run_id_str] = []
    RUN_EVENT_QUEUES[run_id_str].append(queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 1. Replay historical events
            for log in past_logs:
                resp = StoreEventResponse(
                    retailer_id=log.retailer_id,
                    state=log.to_state,
                    from_state=log.from_state,
                    to_state=log.to_state,
                    progress_pct=log.progress_pct,
                    message=log.message,
                    action_type=log.action_type,
                    resume_token=log.resume_token,
                    event_id=str(log.id),
                    timestamp=log.created_at.isoformat(),
                )
                yield f"data: {resp.model_dump_json()}\n\n"

            # 2. Stream live events
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event: StoreStateEvent = await asyncio.wait_for(queue.get(), timeout=1.0)
                    resp = StoreEventResponse(
                        retailer_id=event.retailer_id,
                        state=event.state.value if isinstance(event.state, StoreState) else str(event.state),
                        from_state=str(
                            event.from_state.value
                            if isinstance(event.from_state, StoreState)
                            else (event.from_state or "")
                        ),
                        to_state=str(
                            event.to_state.value if isinstance(event.to_state, StoreState) else (event.to_state or "")
                        ),
                        progress_pct=event.progress_pct,
                        message=event.detail or "",
                        action_type=event.challenge_type,
                        resume_token=event.resume_token,
                        event_id=str(event.quote_id or uuid.uuid4()),
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                    yield f"data: {resp.model_dump_json()}\n\n"
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if run_id_str in RUN_EVENT_QUEUES and queue in RUN_EVENT_QUEUES[run_id_str]:
                RUN_EVENT_QUEUES[run_id_str].remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/quotes/{quote_id}", response_model=StoreQuoteRead)
def get_quote(quote_id: UUID, session: Session = Depends(get_session)):
    quote = session.get(StoreQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store quote not found")
    return quote


@router.post("/quotes/{quote_id}/select-slot", response_model=StoreQuoteRead)
def select_delivery_slot(
    quote_id: UUID,
    slot_req: SelectSlotRequest,
    session: Session = Depends(get_session),
):
    quote = session.get(StoreQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store quote not found")

    quote.selected_delivery_slot_id = slot_req.slot_id
    lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == quote_id)).all()

    raw_fingerprint_lines = [
        {
            "sku": ql.retailer_sku,
            "quantity": ql.packs_added,
            "unit_price_cents": ql.unit_price_cents,
            "line_total_cents": ql.line_total_cents,
        }
        for ql in lines
        if ql.packs_added > 0
    ]
    fees_total = quote.delivery_fee_cents + quote.service_fee_cents + quote.bag_fee_cents + quote.slot_fee_cents
    new_fp = compute_quote_fingerprint(
        retailer_id=quote.retailer_id,
        lines=raw_fingerprint_lines,
        delivery_slot_id=slot_req.slot_id,
        subtotal_cents=quote.subtotal_cents,
        fees_total_cents=fees_total,
        gross_total_cents=quote.gross_total_cents,
    )
    quote.cart_fingerprint = new_fp
    session.add(quote)

    # Record quote revision (PR-05)
    revisions = session.exec(select(QuoteRevision).where(QuoteRevision.quote_id == quote_id)).all()
    new_rev = QuoteRevision(
        quote_id=quote.id,
        revision_number=len(revisions) + 1,
        cart_fingerprint=new_fp,
        subtotal_cents=quote.subtotal_cents,
        gross_total_cents=quote.gross_total_cents,
        selected_delivery_slot_id=slot_req.slot_id,
    )
    session.add(new_rev)
    session.commit()
    session.refresh(quote)
    return quote
