import asyncio
import os
from pathlib import Path
from typing import Dict, Optional


class SessionManager:
    """
    Manages isolated persistent browser profiles per retailer.
    Enforces one concurrency lock per store and never uses stealth or WAF bypass hacks.
    """

    def __init__(self, base_profile_dir: Optional[str] = None):
        self.base_profile_dir = Path(base_profile_dir or os.path.expanduser("~/.profiles"))
        self.base_profile_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}

    def get_profile_path(self, retailer_id: str) -> Path:
        profile_path = self.base_profile_dir / retailer_id.lower().strip()
        profile_path.mkdir(parents=True, exist_ok=True)
        return profile_path

    def get_retailer_lock(self, retailer_id: str) -> asyncio.Lock:
        store = retailer_id.lower().strip()
        if store not in self._locks:
            self._locks[store] = asyncio.Lock()
        return self._locks[store]

    def has_existing_session(self, retailer_id: str) -> bool:
        path = self.get_profile_path(retailer_id)
        # Check if profile directory contains cookies or session state
        return any(path.iterdir())
