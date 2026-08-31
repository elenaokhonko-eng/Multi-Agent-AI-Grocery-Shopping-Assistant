import hashlib
import json
from typing import Any


def build_canonical_payload_v2(
    retailer_id: str,
    lines: list[dict[str, Any]],
    subtotal_cents: int,
    gross_total_cents: int,
    delivery_slot_id: str | None = "std_slot",
    delivery_slot_window: str | None = None,
    retailer_cart_id: str | None = None,
    currency: str = "SGD",
    promotions_discount_cents: int = 0,
    delivery_fee_cents: int = 0,
    service_fee_cents: int = 0,
    bag_fee_cents: int = 0,
    slot_fee_cents: int = 0,
    fees_total_cents: int | None = None,
) -> dict[str, Any]:
    """
    Builds the canonical Fingerprint v2 payload dict.
    """
    normalized_lines = []
    for line in sorted(lines, key=lambda x: str(x.get("retailer_sku", x.get("sku", ""))).strip()):
        sku = str(line.get("retailer_sku", line.get("sku", ""))).strip()
        qty = int(line.get("quantity", line.get("packs_added", 1)))
        unit_price = int(line.get("unit_price_cents", 0))
        line_total = int(line.get("line_total_cents", unit_price * qty))
        normalized_lines.append(
            {
                "sku": sku,
                "quantity": qty,
                "unit_price_cents": unit_price,
                "line_total_cents": line_total,
            }
        )

    # If itemized fees are 0 but fees_total_cents was provided (legacy call), map it to delivery_fee_cents
    if fees_total_cents is not None and (
        delivery_fee_cents == 0 and service_fee_cents == 0 and bag_fee_cents == 0 and slot_fee_cents == 0
    ):
        delivery_fee_cents = fees_total_cents

    calculated_fees_total = delivery_fee_cents + service_fee_cents + bag_fee_cents + slot_fee_cents

    return {
        "schema_version": 2,
        "currency": currency.upper().strip(),
        "retailer_id": str(retailer_id).lower().strip(),
        "retailer_cart_id": str(retailer_cart_id).strip() if retailer_cart_id else None,
        "lines": normalized_lines,
        "promotions_discount_cents": int(promotions_discount_cents),
        "fees": {
            "delivery_fee_cents": int(delivery_fee_cents),
            "service_fee_cents": int(service_fee_cents),
            "bag_fee_cents": int(bag_fee_cents),
            "slot_fee_cents": int(slot_fee_cents),
            "fees_total_cents": int(calculated_fees_total),
        },
        "selected_delivery_slot_id": str(delivery_slot_id).strip() if delivery_slot_id else None,
        "selected_delivery_slot_window": str(delivery_slot_window).strip() if delivery_slot_window else None,
        "subtotal_cents": int(subtotal_cents),
        "gross_total_cents": int(gross_total_cents),
    }


def compute_quote_fingerprint(
    retailer_id: str,
    lines: list[dict[str, Any]],
    delivery_slot_id: str = "std_slot",
    subtotal_cents: int = 0,
    fees_total_cents: int = 0,
    gross_total_cents: int = 0,
    *,
    retailer_cart_id: str | None = None,
    currency: str = "SGD",
    promotions_discount_cents: int = 0,
    delivery_fee_cents: int = 0,
    service_fee_cents: int = 0,
    bag_fee_cents: int = 0,
    slot_fee_cents: int = 0,
    delivery_slot_window: str | None = None,
) -> str:
    """
    Computes deterministic SHA-256 fingerprint for a quote payload.
    """
    payload = build_canonical_payload_v2(
        retailer_id=retailer_id,
        lines=lines,
        subtotal_cents=subtotal_cents,
        gross_total_cents=gross_total_cents,
        delivery_slot_id=delivery_slot_id,
        delivery_slot_window=delivery_slot_window,
        retailer_cart_id=retailer_cart_id,
        currency=currency,
        promotions_discount_cents=promotions_discount_cents,
        delivery_fee_cents=delivery_fee_cents,
        service_fee_cents=service_fee_cents,
        bag_fee_cents=bag_fee_cents,
        slot_fee_cents=slot_fee_cents,
        fees_total_cents=fees_total_cents,
    )
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_quote_fingerprint_v2(
    retailer_id: str,
    lines: list[dict[str, Any]],
    subtotal_cents: int,
    gross_total_cents: int,
    *,
    delivery_slot_id: str | None = "std_slot",
    delivery_slot_window: str | None = None,
    retailer_cart_id: str | None = None,
    currency: str = "SGD",
    promotions_discount_cents: int = 0,
    delivery_fee_cents: int = 0,
    service_fee_cents: int = 0,
    bag_fee_cents: int = 0,
    slot_fee_cents: int = 0,
    fees_total_cents: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Computes Fingerprint v2 and returns both the hex digest and the canonical payload.
    """
    payload = build_canonical_payload_v2(
        retailer_id=retailer_id,
        lines=lines,
        subtotal_cents=subtotal_cents,
        gross_total_cents=gross_total_cents,
        delivery_slot_id=delivery_slot_id,
        delivery_slot_window=delivery_slot_window,
        retailer_cart_id=retailer_cart_id,
        currency=currency,
        promotions_discount_cents=promotions_discount_cents,
        delivery_fee_cents=delivery_fee_cents,
        service_fee_cents=service_fee_cents,
        bag_fee_cents=bag_fee_cents,
        slot_fee_cents=slot_fee_cents,
        fees_total_cents=fees_total_cents,
    )
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return digest, payload


def explain_fingerprint_diff(payload_a: dict[str, Any], payload_b: dict[str, Any]) -> list[str]:
    """
    Produces a human-readable list of differences between two canonical fingerprint payloads.
    """
    diffs = []
    if payload_a.get("retailer_id") != payload_b.get("retailer_id"):
        diffs.append(f"Retailer mismatch: {payload_a.get('retailer_id')} vs {payload_b.get('retailer_id')}")

    if payload_a.get("gross_total_cents") != payload_b.get("gross_total_cents"):
        diffs.append(
            f"Gross total changed from ${payload_a.get('gross_total_cents', 0)/100:.2f} "
            f"to ${payload_b.get('gross_total_cents', 0)/100:.2f}"
        )

    if payload_a.get("subtotal_cents") != payload_b.get("subtotal_cents"):
        diffs.append(
            f"Subtotal changed from ${payload_a.get('subtotal_cents', 0)/100:.2f} "
            f"to ${payload_b.get('subtotal_cents', 0)/100:.2f}"
        )

    if payload_a.get("selected_delivery_slot_id") != payload_b.get("selected_delivery_slot_id"):
        diffs.append(
            f"Slot ID changed from '{payload_a.get('selected_delivery_slot_id')}' "
            f"to '{payload_b.get('selected_delivery_slot_id')}'"
        )

    # Line comparison
    lines_a = {item["sku"]: item for item in payload_a.get("lines", [])}
    lines_b = {item["sku"]: item for item in payload_b.get("lines", [])}

    added_skus = set(lines_b.keys()) - set(lines_a.keys())
    removed_skus = set(lines_a.keys()) - set(lines_b.keys())

    for sku in added_skus:
        diffs.append(f"Added item in live cart: SKU {sku} (qty {lines_b[sku]['quantity']})")
    for sku in removed_skus:
        diffs.append(f"Missing item from live cart: SKU {sku}")

    common_skus = set(lines_a.keys()) & set(lines_b.keys())
    for sku in common_skus:
        la, lb = lines_a[sku], lines_b[sku]
        if la["quantity"] != lb["quantity"]:
            diffs.append(f"Quantity changed for SKU {sku}: {la['quantity']} -> {lb['quantity']}")
        if la["unit_price_cents"] != lb["unit_price_cents"]:
            diffs.append(
                f"Unit price changed for SKU {sku}: ${la['unit_price_cents']/100:.2f} -> ${lb['unit_price_cents']/100:.2f}"
            )

    return diffs
