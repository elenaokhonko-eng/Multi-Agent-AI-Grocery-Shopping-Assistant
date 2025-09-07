# core/profile_store.py
from __future__ import annotations
import os, json, time
from typing import Any, Dict
from core.user_profile import UserProfile, get_default_profile

class UserProfileStore:
    def __init__(self, path: str = ".profiles"):
        os.makedirs(path, exist_ok=True)
        self.path = path

    def _file(self, user_id: str) -> str:
        return os.path.join(self.path, f"{user_id}.json")

    def load(self, user_id: str) -> UserProfile:
        p = self._file(user_id)
        if not os.path.exists(p):
            prof = get_default_profile()
            prof.user_id = user_id
            self.save(prof)
            return prof
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # Rehydrate into your dataclasses (robust to missing keys)
        prof = get_default_profile()
        for k, v in raw.items():
            if hasattr(prof, k):
                cur = getattr(prof, k)
                # simple merge for nested dataclasses
                if hasattr(cur, "__dict__") and isinstance(v, dict):
                    cur.__dict__.update(v)
                else:
                    setattr(prof, k, v)
        return prof

    def save(self, profile: UserProfile):
        # convert dataclasses to dicts
        def to_dict(obj: Any):
            if hasattr(obj, "__dict__"):
                d = {}
                for k, v in obj.__dict__.items():
                    d[k] = to_dict(v)
                return d
            if isinstance(obj, list):
                return [to_dict(x) for x in obj]
            if isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            return obj

        data = to_dict(profile)
        data["_saved_at"] = time.time()
        with open(self._file(profile.user_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
