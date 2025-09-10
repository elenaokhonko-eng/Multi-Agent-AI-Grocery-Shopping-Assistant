# core/feedback.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
import json, os, time

@dataclass
class FeedbackEvent:
    user_id: str
    timestamp: float
    query: str = ""
    category: Optional[str] = None
    item_id: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    store: Optional[str] = None
    price_lkr: Optional[float] = None
    delivery_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    action: str = "click"            # click | like | dislike | add_to_cart | purchase | hide
    rating: Optional[int] = None     # 1..5

@dataclass
class UserPreferences:
    brand_beta: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(lambda: [1,1]))
    store_beta: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(lambda: [1,1]))
    category_beta: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(lambda: [1,1]))
    tag_scores: Dict[str, float] = field(default_factory=dict)
    price_mean: Dict[str, float] = field(default_factory=dict)
    price_var: Dict[str, float] = field(default_factory=dict)
    delivery_mean_h: float = 48.0
    last_updated: float = field(default_factory=time.time)

class PreferenceStore:
    def __init__(self, path: str = ".prefs"):
        os.makedirs(path, exist_ok=True)
        self.path = path
    def _file(self, user_id: str) -> str:
        return os.path.join(self.path, f"{user_id}.json")
    def load(self, user_id: str) -> UserPreferences:
        p = self._file(user_id)
        if not os.path.exists(p): return UserPreferences()
        with open(p, "r", encoding="utf-8") as f: raw = json.load(f)
        up = UserPreferences(); up.__dict__.update(raw); return up
    def save(self, user_id: str, prefs: UserPreferences):
        prefs.last_updated = time.time()
        with open(self._file(user_id), "w", encoding="utf-8") as f:
            json.dump(prefs.__dict__, f, ensure_ascii=False, indent=2)

class FeedbackEngine:
    def __init__(self, store: PreferenceStore, alpha: float = 0.25):
        self.store = store
        self.alpha = alpha
    @staticmethod
    def _ewma(old: float, new: float, a: float): return (1-a)*old + a*new
    @staticmethod
    def _beta_succ(a_b): a_b[0] += 1
    @staticmethod
    def _beta_fail(a_b): a_b[1] += 1

    def record(self, ev: FeedbackEvent):
        prefs = self.store.load(ev.user_id)
        success = ev.action in {"add_to_cart","purchase","like","favourite"}
        negative = ev.action in {"dislike","hide"}

        def upd(d: Dict[str, List[int]], key: Optional[str]):
            if not key: return
            pair = d.setdefault(key, [1,1])
            (self._beta_succ if success else self._beta_fail)(pair)

        upd(prefs.brand_beta, (ev.brand or "").lower() or None)
        upd(prefs.store_beta, (ev.store or "").lower() or None)
        upd(prefs.category_beta, (ev.category or "").lower() or None)

        if ev.tags:
            delta = 1.0 if success else (-1.0 if negative else 0.0)
            if delta:
                for t in ev.tags:
                    prefs.tag_scores[t.lower()] = self._ewma(prefs.tag_scores.get(t.lower(), 0.0), delta, self.alpha)

        if ev.price_lkr and ev.category:
            c = (ev.category or "general").lower()
            mu = prefs.price_mean.get(c, ev.price_lkr)
            mu2 = self._ewma(mu, ev.price_lkr, self.alpha)
            prefs.price_mean[c] = mu2
            spread = prefs.price_var.get(c, 0.0)
            prefs.price_var[c] = self._ewma(spread, abs(ev.price_lkr - mu2), self.alpha)

        if ev.delivery_hours:
            prefs.delivery_mean_h = self._ewma(prefs.delivery_mean_h, ev.delivery_hours, self.alpha)

        if ev.rating:
            w = (ev.rating - 3) / 2.0  # -1..+1
            for t in ev.tags:
                k = t.lower()
                prefs.tag_scores[k] = self._ewma(prefs.tag_scores.get(k, 0.0), w, self.alpha)

        self.store.save(ev.user_id, prefs)

    def snapshot(self, user_id: str) -> UserPreferences:
        return self.store.load(user_id)

    def reset(self, user_id: str):
        self.store.save(user_id, UserPreferences())
