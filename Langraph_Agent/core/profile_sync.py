# core/profile_sync.py
from __future__ import annotations
from typing import List, Tuple
from core.user_profile import UserProfile
from core.feedback import UserPreferences as LearnedPrefs  # from your feedback.py

PREFERRED_TH = 0.65     # Beta mean threshold to mark "preferred"
DISLIKED_TH  = 0.35     # Beta mean threshold to mark "disliked"
MIN_EVIDENCE = 6        # require alpha+beta at least this

def _beta_mean(a_b: List[int]) -> float:
    a, b = a_b
    return a / (a + b)

def _evidence(a_b: List[int]) -> int:
    a, b = a_b
    return int(a + b)

def _merge_unique(dst: List[str], src: List[str]) -> List[str]:
    sdst = {x.lower(): x for x in dst}
    for x in src:
        lx = x.lower()
        if lx not in sdst:
            sdst[lx] = x
    return list(sdst.values())

def augment_profile_from_learned(profile: UserProfile, prefs: LearnedPrefs, *, allow_overwrite=False) -> UserProfile:
    """
    Mutates `profile` in-place using learned preferences.
    Set allow_overwrite=True to also remove items that no longer meet thresholds.
    """
    # 1) Brands → preferred / disliked lists
    learned_pref_brands: List[str] = []
    learned_disliked_brands: List[str] = []

    for brand, ab in (prefs.brand_beta or {}).items():
        if not brand:
            continue
        if _evidence(ab) < MIN_EVIDENCE:
            continue
        mean = _beta_mean(ab)
        if mean >= PREFERRED_TH:
            learned_pref_brands.append(brand)
        elif mean <= DISLIKED_TH:
            learned_disliked_brands.append(brand)

    bp = profile.brand_preferences
    bp.preferred_brands = _merge_unique(bp.preferred_brands, learned_pref_brands)
    bp.disliked_brands  = _merge_unique(bp.disliked_brands, learned_disliked_brands)

    if allow_overwrite:
        # Optional cleanup: remove brands that fell out of threshold
        def keep_pref(b):
            ab = prefs.brand_beta.get(b.lower())
            return ab and _evidence(ab) >= MIN_EVIDENCE and _beta_mean(ab) >= PREFERRED_TH
        def keep_dis(b):
            ab = prefs.brand_beta.get(b.lower())
            return ab and _evidence(ab) >= MIN_EVIDENCE and _beta_mean(ab) <= DISLIKED_TH
        bp.preferred_brands = [b for b in bp.preferred_brands if keep_pref(b)]
        bp.disliked_brands  = [b for b in bp.disliked_brands  if keep_dis(b)]

    # 2) Stores → loyalty preferred stores
    learned_pref_stores: List[str] = []
    for store, ab in (prefs.store_beta or {}).items():
        if not store:
            continue
        if _evidence(ab) < MIN_EVIDENCE:
            continue
        if _beta_mean(ab) >= PREFERRED_TH:
            learned_pref_stores.append(store)

    lm = profile.loyalty_membership
    lm.preferred_stores = _merge_unique(lm.preferred_stores, learned_pref_stores)

    if allow_overwrite:
        def keep_store(s):
            ab = prefs.store_beta.get(s.lower())
            return ab and _evidence(ab) >= MIN_EVIDENCE and _beta_mean(ab) >= PREFERRED_TH
        lm.preferred_stores = [s for s in lm.preferred_stores if keep_store(s)]

    # 3) Delivery preference → nudge max_delivery_time_hours toward learned mean
    # If user has not explicitly constrained it tightly, adapt slightly.
    if hasattr(profile, "delivery_preferences") and prefs.delivery_mean_h:
        cur = profile.delivery_preferences.max_delivery_time_hours
        learned = prefs.delivery_mean_h
        # Keep it user-friendly: cap change and keep some headroom (25%)
        target = int(round(min(cur, max(learned, 6)) * 1.0))  # don’t worsen; min 6h
        profile.delivery_preferences.max_delivery_time_hours = target

    return profile
