from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from domain.services.units import (
    NormalizedPack,
    calculate_dimension_packs,
    parse_normalized_pack,
    validate_pack_bounds,
)


class MatchStatus(str, Enum):
    EXACT = "EXACT"
    ALLOWED_SUBSTITUTION = "ALLOWED_SUBSTITUTION"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECTED = "REJECTED"


@dataclass
class PackSpecification:
    amount: float
    unit: str
    raw_text: str


PRODUCE_NEGATIVE_KEYWORDS = [
    "detergent",
    "dishwash",
    "dishwashing",
    "soap",
    "bleach",
    "cleaner",
    "shampoo",
    "conditioner",
    "candle",
    "fragrance",
    "tea",
    "tea bag",
    "air freshener",
    "scented",
    "wipes",
    "sanitizer",
    "disinfectant",
    "beverage",
    "drink",
]

STOP_WORDS = {"fresh", "organic", "the", "and", "a", "an", "of", "in", "pack", "item", "super"}


def parse_pack_size(text: str) -> PackSpecification | None:
    """Extract structured pack specification from product title or pack size string."""
    norm = parse_normalized_pack(text)
    if not norm:
        return None
    return PackSpecification(
        amount=norm.display_amount,
        unit=norm.display_unit,
        raw_text=norm.raw_text,
    )


def is_excluded_by_negative_filter(
    title: str,
    category: str | None = None,
    exclusions: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Check if a candidate product violates negative exclusion keywords.
    E.g. Lemon search must reject lemon dishwash, lemon scented wipes, lemon tea.
    """
    title_lower = title.lower()
    cat_lower = (category or "").lower()

    # User-defined custom exclusions
    if exclusions:
        for exc in exclusions:
            if not exc:
                continue
            exc_clean = exc.lower().strip()
            # Word boundary check for user exclusions
            if re.search(rf"\b{re.escape(exc_clean)}\b", title_lower):
                return True, f"Excluded by user rule: '{exc}'"

    # Category and keyword hygiene for produce
    if any(
        re.search(rf"\b{k}\b", title_lower)
        for k in ["lemon", "lemons", "lime", "limes", "orange", "apple", "produce", "fresh"]
    ):
        for non_food in PRODUCE_NEGATIVE_KEYWORDS:
            if re.search(rf"\b{re.escape(non_food)}\b", title_lower) or non_food in cat_lower:
                return True, f"Excluded non-food match containing '{non_food}'"

    return False, None


def calculate_required_packs(
    desired_qty: float | int,
    desired_unit: str,
    product_pack: PackSpecification | NormalizedPack | None,
) -> tuple[int, str | None]:
    """Calculate the exact number of packs to buy with ceil rounding."""
    if isinstance(product_pack, PackSpecification):
        norm_pack = parse_normalized_pack(f"{product_pack.amount}{product_pack.unit}")
    else:
        norm_pack = product_pack

    return calculate_dimension_packs(desired_qty, desired_unit, norm_pack)


def match_product_candidate(
    candidate_title: str,
    candidate_sku: str,
    candidate_brand: str | None,
    candidate_category: str | None,
    candidate_pack: str | None,
    item_spec: dict[str, Any],
) -> tuple[bool, int, str | None]:
    """
    Evaluates a candidate product against shopping item specifications.
    Returns (is_match, packs_to_add, rejection_reason).
    """
    desired_qty = item_spec.get("desired_quantity", 1)
    desired_unit = item_spec.get("unit_measure", "pack")
    pack_spec = parse_normalized_pack(candidate_pack or candidate_title)

    # 1. Check pinned SKU override
    pinned_skus = item_spec.get("pinned_skus") or {}
    for pinned in pinned_skus.values():
        if pinned and pinned.strip() == candidate_sku.strip():
            # Calculate packs properly based on pinned item pack size & desired quantity
            packs_to_add, err = calculate_dimension_packs(desired_qty, desired_unit, pack_spec)
            if err and "DIMENSIONAL_MISMATCH" in err:
                return False, 0, err
            return True, max(1, packs_to_add), None

    # 2. Check Negative Exclusions
    exclusions = item_spec.get("exclusions") or []
    is_excluded, exc_reason = is_excluded_by_negative_filter(
        candidate_title,
        category=candidate_category,
        exclusions=exclusions,
    )
    if is_excluded:
        return False, 0, exc_reason

    # 3. Check Name Token Overlap with strict word boundaries
    item_name = item_spec.get("name", "").lower()
    item_tokens = [t for t in re.findall(r"\b\w+\b", item_name) if t not in STOP_WORDS]
    if item_tokens:
        cand_title_lower = candidate_title.lower()
        cand_cat_lower = (candidate_category or "").lower()
        has_token_match = any(
            re.search(rf"\b{re.escape(t)}\b", cand_title_lower) or re.search(rf"\b{re.escape(t)}\b", cand_cat_lower)
            for t in item_tokens
        )
        if not has_token_match:
            return False, 0, f"No keyword overlap with '{item_name}'"

    # 4. Check Preferred Brand rules if substitution policy is SAME_BRAND_ONLY
    pref_brands = [b.lower().strip() for b in (item_spec.get("preferred_brands") or []) if b]
    sub_policy = item_spec.get("substitution_policy", "SAME_BRAND_ONLY")
    if sub_policy == "SAME_BRAND_ONLY" and pref_brands:
        cand_brand_norm = (candidate_brand or "").lower().strip()
        cand_title_norm = candidate_title.lower()
        has_brand_match = any(
            re.search(rf"\b{re.escape(b)}\b", cand_brand_norm) or re.search(rf"\b{re.escape(b)}\b", cand_title_norm)
            for b in pref_brands
        )
        if not has_brand_match:
            return False, 0, f"Brand mismatch for {pref_brands}"

    # 5. Validate Pack Bounds (Min / Max pack size)
    min_pack_str = item_spec.get("min_pack_size")
    max_pack_str = item_spec.get("max_pack_size")
    bounds_valid, bounds_err = validate_pack_bounds(pack_spec, min_pack_str, max_pack_str)
    if not bounds_valid:
        return False, 0, bounds_err

    # 6. Calculate required packs with dimension compatibility check
    packs_to_add, dim_err = calculate_dimension_packs(desired_qty, desired_unit, pack_spec)
    if dim_err:
        return False, 0, dim_err

    return True, packs_to_add, None
