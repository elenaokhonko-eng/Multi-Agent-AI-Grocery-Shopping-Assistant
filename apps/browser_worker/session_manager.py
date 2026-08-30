import asyncio
import os
import stat
from pathlib import Path


class SessionManager:
    """
    Manages isolated persistent browser profiles per retailer.
    Enforces one concurrency lock per store, directory permissions 0700, and never uses stealth or WAF bypass hacks.
    """

    def __init__(self, base_profile_dir: str | None = None):
        default_dir = os.getenv(
            "GROCERY_BROWSER_PROFILE_DIR",
            os.path.expanduser("~/.grocery_assistant/browser_profiles"),
        )
        self.base_profile_dir = Path(base_profile_dir or default_dir)
        self.base_profile_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_secure_permissions(self.base_profile_dir)
        self._locks: dict[str, asyncio.Lock] = {}

    def _ensure_secure_permissions(self, path: Path) -> None:
        try:
            if hasattr(os, "chmod") and os.name != "nt":
                os.chmod(path, stat.S_IRWXU)  # 0700: Owner RWX only
        except Exception:
            pass

    def get_profile_path(self, retailer_id: str) -> Path:
        profile_path = self.base_profile_dir / retailer_id.lower().strip()
        profile_path.mkdir(parents=True, exist_ok=True)
        self._ensure_secure_permissions(profile_path)
        return profile_path

    def get_retailer_lock(self, retailer_id: str) -> asyncio.Lock:
        store = retailer_id.lower().strip()
        if store not in self._locks:
            self._locks[store] = asyncio.Lock()
        return self._locks[store]

    def has_existing_session(self, retailer_id: str) -> bool:
        path = self.get_profile_path(retailer_id)
        if not path.exists():
            return False
        return any(path.iterdir())
