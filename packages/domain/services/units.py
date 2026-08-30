from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Dimension(str, Enum):
    COUNT = "COUNT"
    MASS = "MASS"
    VOLUME = "VOLUME"


UNIT_MAPPINGS: dict[str, tuple[Dimension, float, str]] = {
    # Count dimension (Base = EACH)
    "each": (Dimension.COUNT, 1.0, "each"),
    "piece": (Dimension.COUNT, 1.0, "piece"),
    "pieces": (Dimension.COUNT, 1.0, "pieces"),
    "pcs": (Dimension.COUNT, 1.0, "pcs"),
    "unit": (Dimension.COUNT, 1.0, "unit"),
    "units": (Dimension.COUNT, 1.0, "units"),
    "item": (Dimension.COUNT, 1.0, "item"),
    "items": (Dimension.COUNT, 1.0, "items"),
    "s": (Dimension.COUNT, 1.0, "s"),
    "pack": (Dimension.COUNT, 1.0, "pack"),
    "pk": (Dimension.COUNT, 1.0, "pk"),
    # Mass dimension (Base = G)
    "g": (Dimension.MASS, 1.0, "g"),
    "gram": (Dimension.MASS, 1.0, "g"),
    "grams": (Dimension.MASS, 1.0, "g"),
    "kg": (Dimension.MASS, 1000.0, "kg"),
    "kilogram": (Dimension.MASS, 1000.0, "kg"),
    "kilograms": (Dimension.MASS, 1000.0, "kg"),
    # Volume dimension (Base = ML)
    "ml": (Dimension.VOLUME, 1.0, "ml"),
    "milliliter": (Dimension.VOLUME, 1.0, "ml"),
    "millilitre": (Dimension.VOLUME, 1.0, "ml"),
    "l": (Dimension.VOLUME, 1000.0, "L"),
    "liter": (Dimension.VOLUME, 1000.0, "L"),
    "litres": (Dimension.VOLUME, 1000.0, "L"),
    "litre": (Dimension.VOLUME, 1000.0, "L"),
    "liters": (Dimension.VOLUME, 1000.0, "L"),
}


@dataclass
class NormalizedPack:
    dimension: Dimension
    base_amount: float  # g for MASS, ml for VOLUME, count for COUNT
    display_amount: float
    display_unit: str
    multipack_count: int = 1
    raw_text: str = ""
    parse_confidence: float = 1.0


# Regex patterns
MULTIPACK_RE = re.compile(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(kg|g|l|ml|s|pcs|pieces|pack|pk)?", re.IGNORECASE)
STANDARD_PACK_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g|l|ml|pcs|pieces|pack|pk|'s|s)\b", re.IGNORECASE)
PACK_OF_N_RE = re.compile(r"pack\s*of\s*(\d+)", re.IGNORECASE)


def normalize_unit_string(unit_str: str) -> tuple[Dimension, float, str] | None:
    norm = unit_str.lower().strip().rstrip(".")
    return UNIT_MAPPINGS.get(norm)


def parse_normalized_pack(text: str) -> NormalizedPack | None:
    """Parses any product description or pack size into a structured NormalizedPack."""
    if not text:
        return None

    clean = text.strip()

    # 1. Multipack pattern: e.g. "3 x 250ml"
    m_match = MULTIPACK_RE.search(clean)
    if m_match:
        count = int(m_match.group(1))
        item_amount = float(m_match.group(2))
        unit_raw = (m_match.group(3) or "pack").lower()
        mapping = normalize_unit_string(unit_raw) or (Dimension.COUNT, 1.0, "pack")
        dim, multiplier, canonical_display_unit = mapping
        base_amount = count * item_amount * multiplier

        return NormalizedPack(
            dimension=dim,
            base_amount=base_amount,
            display_amount=count * item_amount,
            display_unit=canonical_display_unit,
            multipack_count=count,
            raw_text=m_match.group(0),
            parse_confidence=0.95,
        )

    # 2. Pack of N pattern: e.g. "pack of 3"
    p_match = PACK_OF_N_RE.search(clean)
    if p_match:
        count = int(p_match.group(1))
        return NormalizedPack(
            dimension=Dimension.COUNT,
            base_amount=float(count),
            display_amount=float(count),
            display_unit="pieces",
            multipack_count=1,
            raw_text=p_match.group(0),
            parse_confidence=0.9,
        )

    # 3. Standard weight/volume/count: e.g. "2L", "500g", "10s", "3 pieces"
    s_match = STANDARD_PACK_RE.search(clean)
    if s_match:
        amount = float(s_match.group(1))
        unit_raw = s_match.group(2).lower().lstrip("'")
        std_mapping = normalize_unit_string(unit_raw)
        if std_mapping is not None:
            dim, multiplier, canonical_display_unit = std_mapping
            return NormalizedPack(
                dimension=dim,
                base_amount=amount * multiplier,
                display_amount=amount,
                display_unit=canonical_display_unit,
                multipack_count=1,
                raw_text=s_match.group(0),
                parse_confidence=0.9,
            )

    return None


def calculate_dimension_packs(
    desired_quantity: float | Decimal | int,
    desired_unit: str,
    product_pack: NormalizedPack | None,
) -> tuple[int, str | None]:
    """
    Deterministically calculates the exact required packs with ceil rounding.
    Rejects dimensional mismatches (e.g. mass requested vs volume candidate).
    """
    desired_qty_f = float(desired_quantity)
    if desired_qty_f <= 0:
        return 0, "Desired quantity must be positive"

    desired_mapping = normalize_unit_string(desired_unit)
    if not desired_mapping:
        # Default 1:1 if unit cannot be mapped
        return max(1, math.ceil(desired_qty_f)), None

    desired_dim, desired_mult, _ = desired_mapping
    desired_base_amount = desired_qty_f * desired_mult

    if not product_pack:
        return max(1, math.ceil(desired_qty_f)), None

    # Check dimensional compatibility
    if product_pack.dimension != desired_dim:
        return 0, (
            f"DIMENSIONAL_MISMATCH: Requested {desired_unit} ({desired_dim.value}) "
            f"cannot match candidate {product_pack.display_unit} ({product_pack.dimension.value})"
        )

    if product_pack.base_amount <= 0:
        return max(1, math.ceil(desired_qty_f)), None

    # Calculate exact packs with ceil
    packs = max(1, math.ceil(desired_base_amount / product_pack.base_amount))
    return packs, None


def validate_pack_bounds(
    candidate_pack: NormalizedPack | None,
    min_pack_str: str | None,
    max_pack_str: str | None,
) -> tuple[bool, str | None]:
    """Validates candidate pack size against min/max bounds in the same dimension."""
    if not candidate_pack:
        return True, None

    if min_pack_str:
        min_pack = parse_normalized_pack(min_pack_str)
        if min_pack:
            if min_pack.dimension != candidate_pack.dimension:
                return False, (
                    f"Min pack bound dimension mismatch: {min_pack_str} ({min_pack.dimension.value}) "
                    f"vs {candidate_pack.display_unit} ({candidate_pack.dimension.value})"
                )
            if candidate_pack.base_amount < min_pack.base_amount:
                return False, (
                    f"Candidate pack {candidate_pack.display_amount}{candidate_pack.display_unit} "
                    f"is below minimum bound {min_pack_str}"
                )

    if max_pack_str:
        max_pack = parse_normalized_pack(max_pack_str)
        if max_pack:
            if max_pack.dimension != candidate_pack.dimension:
                return False, (
                    f"Max pack bound dimension mismatch: {max_pack_str} ({max_pack.dimension.value}) "
                    f"vs {candidate_pack.display_unit} ({candidate_pack.dimension.value})"
                )
            if candidate_pack.base_amount > max_pack.base_amount:
                return False, (
                    f"Candidate pack {candidate_pack.display_amount}{candidate_pack.display_unit} "
                    f"exceeds maximum bound {max_pack_str}"
                )

    return True, None
