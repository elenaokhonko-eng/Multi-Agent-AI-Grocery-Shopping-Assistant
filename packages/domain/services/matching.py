import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class PackSpecification:
    amount: float
    unit: str  # 'g', 'kg', 'ml', 'l', 's', 'pack', 'pcs'
    raw_text: str


# Regex patterns for various supermarket pack descriptions
PACK_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g|l|ml)\b", re.IGNORECASE),
    re.compile(r"(\d+)\s*(?:'s|s|pcs|pieces|pack|pk)\b", re.IGNORECASE),
    re.compile(r"pack\s*of\s*(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(kg|g|l|ml|s)?", re.IGNORECASE),
]

PRODUCE_NEGATIVE_KEYWORDS = [
    "detergent", "dishwash", "dishwashing", "soap", "bleach", "cleaner",
    "shampoo", "conditioner", "candle", "fragrance", "tea", "tea bag", "air freshener",
    "scented", "wipes", "sanitizer", "disinfectant", "beverage", "drink",
]

STOP_WORDS = {"fresh", "organic", "the", "and", "a", "an", "of", "in", "pack", "item", "super"}


def parse_pack_size(text: str) -> PackSpecification | None:
    """Extract structured pack specification from product title or pack size string."""
    if not text:
        return None

    # Check for multipack format (e.g. 3 x 250ml)
    multi_match = re.search(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(kg|g|l|ml|s)?", text, re.IGNORECASE)
    if multi_match:
        count = float(multi_match.group(1))
        size = float(multi_match.group(2))
        unit = (multi_match.group(3) or "unit").lower()
        return PackSpecification(amount=count * size, unit=unit, raw_text=multi_match.group(0))

    # Check standard volume/weight/count patterns
    for pattern in PACK_PATTERNS:
        match = pattern.search(text)
        if match:
            amount = float(match.group(1))
            unit = match.group(2).lower() if len(match.groups()) > 1 and match.group(2) else "s"
            # Normalize units
            if unit in ["pcs", "pieces", "pack", "pk"]:
                unit = "s"
            return PackSpecification(amount=amount, unit=unit, raw_text=match.group(0))

    return None


def is_excluded_by_negative_filter(title: str, category: str | None = None, exclusions: list[str] | None = None) -> tuple[bool, str | None]:
    """
    Check if a candidate product violates negative exclusion keywords.
    E.g. Lemon search must reject lemon dishwash, lemon scented wipes, lemon tea.
    """
    title_lower = title.lower()
    cat_lower = (category or "").lower()

    # User-defined custom exclusions
    if exclusions:
        for exc in exclusions:
            if exc.lower().strip() in title_lower:
                return True, f"Excluded by user rule: '{exc}'"

    # Category and keyword hygiene for produce
    if any(k in title_lower for k in ["lemon", "lime", "orange", "apple", "produce", "fresh"]):
        for non_food in PRODUCE_NEGATIVE_KEYWORDS:
            if non_food in title_lower or non_food in cat_lower:
                return True, f"Excluded non-food match containing '{non_food}'"

    return False, None


def calculate_required_packs(
    desired_qty: int,
    desired_unit: str,
    product_pack: PackSpecification | None
) -> tuple[int, str | None]:
    """
    Calculate the exact number of packs to buy using math.ceil to prevent under-ordering.
    E.g. Desired 3 lemons (unit='pieces'):
    - Single lemon (pack=1s): packs_added = 3
    - 3s pack (pack=3s): packs_added = 1
    """
    unit_norm = desired_unit.lower().strip()

    if not product_pack:
        # Default 1:1 pack mapping if no specific pack size extracted
        return max(1, desired_qty), None

    pack_amount = product_pack.amount
    pack_unit = product_pack.unit

    if pack_amount <= 0:
        return max(1, desired_qty), None

    # If desired in pieces/units and item is sold as a pack of N
    if unit_norm in ["piece", "pieces", "unit", "units", "s", "item", "items"]:
        if pack_unit == "s" and pack_amount > 1:
            packs = max(1, math.ceil(desired_qty / pack_amount))
            return packs, None
        return max(1, desired_qty), None

    # Weight matching (e.g. desired 1kg vs 500g packs)
    if unit_norm == "kg":
        if pack_unit == "g":
            desired_g = desired_qty * 1000.0
            packs = max(1, math.ceil(desired_g / pack_amount))
            return packs, None
        elif pack_unit == "kg":
            packs = max(1, math.ceil(desired_qty / pack_amount))
            return packs, None

    # Volume matching (e.g. desired 2L vs 1L packs)
    if unit_norm in ["l", "liter", "litres"]:
        if pack_unit == "ml":
            desired_ml = desired_qty * 1000.0
            packs = max(1, math.ceil(desired_ml / pack_amount))
            return packs, None
        elif pack_unit == "l":
            packs = max(1, math.ceil(desired_qty / pack_amount))
            return packs, None

    return max(1, desired_qty), None


def match_product_candidate(
    candidate_title: str,
    candidate_sku: str,
    candidate_brand: str | None,
    candidate_category: str | None,
    candidate_pack: str | None,
    item_spec: dict[str, Any]
) -> tuple[bool, int, str | None]:
    """
    Evaluates a candidate product against shopping item specifications.
    Returns (is_match, packs_to_add, rejection_reason).
    """
    # 1. Check pinned SKU override
    pinned_skus = item_spec.get("pinned_skus") or {}
    for pinned in pinned_skus.values():
        if pinned and pinned.strip() == candidate_sku.strip():
            return True, item_spec.get("desired_quantity", 1), None

    # 2. Check Negative Exclusions
    exclusions = item_spec.get("exclusions") or []
    is_excluded, exc_reason = is_excluded_by_negative_filter(
        candidate_title,
        category=candidate_category,
        exclusions=exclusions
    )
    if is_excluded:
        return False, 0, exc_reason

    # 3. Check Name Token Overlap (at least one non-stopword token from item name must match)
    item_name = item_spec.get("name", "").lower()
    item_tokens = [t for t in re.findall(r"\b\w+\b", item_name) if t not in STOP_WORDS]
    if item_tokens:
        cand_title_lower = candidate_title.lower()
        cand_cat_lower = (candidate_category or "").lower()
        has_token_match = any(t in cand_title_lower or t in cand_cat_lower for t in item_tokens)
        if not has_token_match:
            return False, 0, f"No keyword overlap with '{item_name}'"

    # 4. Check Preferred Brand rules if substitution policy is SAME_BRAND_ONLY
    pref_brands = [b.lower().strip() for b in (item_spec.get("preferred_brands") or []) if b]
    sub_policy = item_spec.get("substitution_policy", "SAME_BRAND_ONLY")
    if sub_policy == "SAME_BRAND_ONLY" and pref_brands:
        cand_brand_norm = (candidate_brand or "").lower().strip()
        cand_title_norm = candidate_title.lower()
        has_brand_match = any(b in cand_brand_norm or b in cand_title_norm for b in pref_brands)
        if not has_brand_match:
            return False, 0, f"Brand mismatch for {pref_brands}"

    # 5. Parse Pack Size and check Min/Max pack bounds if specified
    pack_spec = parse_pack_size(candidate_pack or candidate_title)
    if pack_spec:
        min_pack_str = item_spec.get("min_pack_size")
        if min_pack_str:
            min_spec = parse_pack_size(min_pack_str)
            if min_spec and min_spec.unit == pack_spec.unit and pack_spec.amount < min_spec.amount:
                return False, 0, f"Pack size {pack_spec.amount}{pack_spec.unit} below minimum {min_pack_str}"

        max_pack_str = item_spec.get("max_pack_size")
        if max_pack_str:
            max_spec = parse_pack_size(max_pack_str)
            if max_spec and max_spec.unit == pack_spec.unit and pack_spec.amount > max_spec.amount:
                return False, 0, f"Pack size {pack_spec.amount}{pack_spec.unit} exceeds maximum {max_pack_str}"

    # 6. Calculate required packs
    desired_qty = item_spec.get("desired_quantity", 1)
    desired_unit = item_spec.get("unit_measure", "pack")

    packs_to_add, _ = calculate_required_packs(desired_qty, desired_unit, pack_spec)

    return True, packs_to_add, None
