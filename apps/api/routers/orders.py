import inspect
import logging
import os
from datetime import UTC, datetime
from uuid import UUID

from domain.models.core import Approval, OrderReceipt, QuoteLine, StoreQuote, SubmissionAttempt
from domain.services.fingerprint import compute_quote_fingerprint
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from apps.api.core import ADAPTER_MAP, ensure_utc, get_session
from apps.api.schemas import OrderSubmitRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Orders & Checkout"])


async def _call_adapter_submit_order(adapter, approval: Approval, quote: StoreQuote):
    submit_fn = adapter.submit_order
    sig = inspect.signature(submit_fn)
    params = sig.parameters

    kwargs = {}
    if "approval_token" in params:
        kwargs["approval_token"] = approval.approval_token
    if "slot_id" in params:
        kwargs["slot_id"] = approval.delivery_slot_id
    if "quote_id" in params:
        kwargs["quote_id"] = str(quote.id)
    if "delivery_slot_id" in params:
        kwargs["delivery_slot_id"] = approval.delivery_slot_id
    if "cart_fingerprint" in params:
        kwargs["cart_fingerprint"] = approval.expected_fingerprint

    if kwargs:
        return await submit_fn(**kwargs)
    return await submit_fn(approval.approval_token)


@router.post("/approvals/{approval_id}/submit", status_code=status.HTTP_200_OK)
async def submit_order_approval(
    approval_id: UUID,
    submit_req: OrderSubmitRequest,
    session: Session = Depends(get_session),
):
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    if approval.is_used:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This approval token has already been used to submit an order.",
        )

    if ensure_utc(approval.expires_at) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approval token has expired.")

    if approval.approval_token != submit_req.approval_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid approval token")

    quote = session.get(StoreQuote, approval.quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced quote not found")

    if quote.cart_fingerprint != approval.expected_fingerprint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "FINGERPRINT_MISMATCH",
                "message": "Live cart has changed or been tampered with since approval.",
            },
        )

    # Re-verify live cart lines if populated
    lines = session.exec(select(QuoteLine).where(QuoteLine.quote_id == quote.id)).all()
    if lines:
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
        recalculated_fp = compute_quote_fingerprint(
            retailer_id=quote.retailer_id,
            lines=raw_fingerprint_lines,
            delivery_slot_id=approval.delivery_slot_id,
            subtotal_cents=quote.subtotal_cents,
            fees_total_cents=fees_total,
            gross_total_cents=quote.gross_total_cents,
        )
        if recalculated_fp != approval.expected_fingerprint:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "FINGERPRINT_MISMATCH",
                    "message": "Cart has changed since approval. Re-approval required.",
                },
            )

    adapter_cls = ADAPTER_MAP.get(quote.retailer_id)
    if not adapter_cls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported retailer: {quote.retailer_id}"
        )

    adapter = adapter_cls() if callable(adapter_cls) else adapter_cls

    # Revalidate cart with retailer adapter if method exists
    reval_fn = getattr(adapter, "revalidate_cart", None)
    if reval_fn:
        try:
            diff = await reval_fn(quote)
            if diff and getattr(diff, "has_changes", False):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "REAPPROVAL_REQUIRED",
                        "message": "Cart changed during revalidation. Re-approval required.",
                    },
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Revalidation check failed: %s", e)

    # Track submission attempt (PR-05 durable task graph)
    existing_attempts = session.exec(
        select(SubmissionAttempt).where(SubmissionAttempt.approval_id == approval.id)
    ).all()
    attempt = SubmissionAttempt(
        approval_id=approval.id,
        idempotency_key=approval.idempotency_key,
        attempt_number=len(existing_attempts) + 1,
        status="PENDING",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    # Check live purchasing flag
    live_enabled = os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
    if not live_enabled:
        attempt.status = "FAILED"
        attempt.error_detail = "LIVE_CHECKOUT_NOT_IMPLEMENTED"
        attempt.updated_at = datetime.now(UTC)
        session.add(attempt)
        session.commit()
        try:
            receipt_obj = await _call_adapter_submit_order(adapter, approval, quote)
        except NotImplementedError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "LIVE_CHECKOUT_NOT_IMPLEMENTED",
                    "message": f"Live checkout is not yet implemented for {quote.retailer_id}. Please complete in browser.",
                    "retailer_id": quote.retailer_id,
                    "cart_url": quote.cart_url or f"https://www.{quote.retailer_id}.com.sg/cart",
                },
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "LIVE_CHECKOUT_NOT_IMPLEMENTED",
                    "message": f"Live checkout is not yet implemented for {quote.retailer_id}. Please complete in browser.",
                    "retailer_id": quote.retailer_id,
                    "cart_url": quote.cart_url or f"https://www.{quote.retailer_id}.com.sg/cart",
                },
            )
    else:
        try:
            receipt_obj = await _call_adapter_submit_order(adapter, approval, quote)
            attempt.status = "CONFIRMED"
            attempt.retailer_response = receipt_obj.retailer_order_id
            attempt.updated_at = datetime.now(UTC)
            session.add(attempt)
        except Exception as e:
            attempt.status = "UNCERTAIN"
            attempt.error_detail = str(e)
            attempt.updated_at = datetime.now(UTC)
            session.add(attempt)
            session.commit()
            raise

    # Save real order receipt
    approval.is_used = True
    session.add(approval)

    receipt = OrderReceipt(
        approval_id=approval.id,
        retailer_order_id=receipt_obj.retailer_order_id,
        retailer_id=quote.retailer_id,
        confirmed_total_cents=receipt_obj.confirmed_total_cents,
        confirmed_delivery_slot=receipt_obj.delivery_slot,
        receipt_url=receipt_obj.receipt_url,
        placed_at=datetime.now(UTC),
    )
    session.add(receipt)
    session.commit()
    session.refresh(receipt)

    return {
        "status": "CONFIRMED",
        "order_id": str(receipt.id),
        "receipt_id": str(receipt.id),
        "retailer_order_id": receipt.retailer_order_id,
        "retailer_id": receipt.retailer_id,
        "confirmed_total_cents": receipt.confirmed_total_cents,
        "confirmed_delivery_slot": receipt.confirmed_delivery_slot,
        "placed_at": receipt.placed_at,
        "receipt_url": receipt.receipt_url,
    }


@router.get("/orders/{order_id}")
def get_order_receipt(order_id: UUID, session: Session = Depends(get_session)):
    receipt = session.get(OrderReceipt, order_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order receipt not found")
    return receipt
