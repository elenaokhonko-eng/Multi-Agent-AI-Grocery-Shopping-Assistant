import hashlib
import json
from typing import Any


def compute_quote_fingerprint(
    retailer_id: str,
    lines: list[dict[str, Any]],
    delivery_slot_id: str,
    subtotal_cents: int,
    fees_total_cents: int,
    gross_total_cents: int,
) -> str:
    """
    Computes deterministic SHA-256 fingerprint for a normalized quote per ADR-004.
    """
    normalized_lines = []
    for line in sorted(lines, key=lambda x: str(x.get("retailer_sku", "")).strip()):
        normalized_lines.append(
            {
                "sku": str(line.get("retailer_sku", "")).strip(),
                "quantity": int(line.get("quantity", line.get("packs_added", 1))),
                "unit_price_cents": int(line.get("unit_price_cents", 0)),
                "line_total_cents": int(line.get("line_total_cents", 0)),
            }
        )

    canonical_payload = {
        "retailer_id": str(retailer_id).lower().strip(),
        "lines": normalized_lines,
        "delivery_slot_id": str(delivery_slot_id).strip(),
        "subtotal_cents": int(subtotal_cents),
        "fees_total_cents": int(fees_total_cents),
        "gross_total_cents": int(gross_total_cents),
    }

    serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
