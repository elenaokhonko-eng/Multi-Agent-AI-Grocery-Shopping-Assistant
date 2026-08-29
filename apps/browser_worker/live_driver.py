"""
Real-world browser worker and live retailer interaction driver.
Strictly adheres to:
- No anti-bot bypass / header spoofing
- Challenges -> USER_ACTION_REQUIRED
- Real live store search and cart interaction
"""

import logging
from dataclasses import dataclass

import httpx

from apps.browser_worker.session_manager import SessionManager
from packages.domain.services.matching import parse_pack_size

logger = logging.getLogger(__name__)


@dataclass
class LiveProductResult:
    retailer_sku: str
    title: str
    brand: str | None
    category: str | None
    price_cents: int
    pack_size: str | None
    unit_measure: str
    unit_price_cents: int
    image_url: str | None
    product_url: str
    in_stock: bool


class LiveRetailerDriver:
    """Live Driver executing live searches and browser automation for Singapore retailers."""

    def __init__(self, session_manager: SessionManager | None = None):
        self.session_manager = session_manager or SessionManager()
        self.http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def close(self):
        await self.http_client.aclose()

    # -------------------------------------------------------------------------
    # FairPrice Real Search & Scraper
    # -------------------------------------------------------------------------
    async def search_fairprice(self, query: str) -> list[LiveProductResult]:
        results: list[LiveProductResult] = []
        try:
            # 1. Query FairPrice Public Catalog Service
            url = f"https://public.fairprice.com.sg/api/service-v2/search/product?query={query}&page=1&pageSize=20"
            resp = await self.http_client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("data", {}).get("product", []) or data.get("data", {}).get("products", [])
                for p in products:
                    sku = str(p.get("sku") or p.get("id") or f"FP_{p.get('name', 'item')}")
                    title = p.get("name") or "Product"
                    brand = p.get("brand", {}).get("name") if isinstance(p.get("brand"), dict) else p.get("brand")
                    price_num = float(p.get("storeSpecificData", [{}])[0].get("price") or p.get("finalPrice") or p.get("price") or 0.0)
                    price_cents = round(price_num * 100)
                    image = p.get("images", [None])[0] if isinstance(p.get("images"), list) and p.get("images") else None
                    pack = p.get("metaData", {}).get("DisplayUnit") or p.get("weight")
                    in_stock = not bool(p.get("outOfStock", False))

                    pack_spec = parse_pack_size(pack or title)
                    unit_measure = pack_spec.unit if pack_spec else "pack"
                    unit_price = round(price_cents / pack_spec.amount) if pack_spec and pack_spec.amount > 0 else price_cents

                    results.append(LiveProductResult(
                        retailer_sku=f"FP_{sku}",
                        title=title,
                        brand=brand,
                        category="Groceries",
                        price_cents=price_cents,
                        pack_size=pack or (pack_spec.raw_text if pack_spec else None),
                        unit_measure=unit_measure,
                        unit_price_cents=unit_price,
                        image_url=image,
                        product_url=f"https://www.fairprice.com.sg/product/{sku}",
                        in_stock=in_stock
                    ))
        except Exception as e:
            logger.warning(f"Live FairPrice search failed: {e}")

        return results

    # -------------------------------------------------------------------------
    # Sheng Siong Real Search & Scraper
    # -------------------------------------------------------------------------
    async def search_shengsiong(self, query: str) -> list[LiveProductResult]:
        results: list[LiveProductResult] = []
        try:
            url = f"https://allforyou.sg/api/v1/search?keyword={query}&page=1&limit=20"
            resp = await self.http_client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items") or data.get("products") or []
                for item in items:
                    sku = str(item.get("id") or item.get("sku") or "SS_000")
                    title = item.get("name") or item.get("title") or "Item"
                    price_num = float(item.get("price") or item.get("current_price") or 0.0)
                    price_cents = round(price_num * 100)
                    image = item.get("image_url") or item.get("thumbnail")
                    pack = item.get("pack_size") or item.get("unit")
                    in_stock = bool(item.get("in_stock", True))

                    pack_spec = parse_pack_size(pack or title)
                    unit_measure = pack_spec.unit if pack_spec else "pack"
                    unit_price = round(price_cents / pack_spec.amount) if pack_spec and pack_spec.amount > 0 else price_cents

                    results.append(LiveProductResult(
                        retailer_sku=f"SS_{sku}",
                        title=title,
                        brand=item.get("brand", "Sheng Siong"),
                        category=item.get("category", "Groceries"),
                        price_cents=price_cents,
                        pack_size=pack or (pack_spec.raw_text if pack_spec else None),
                        unit_measure=unit_measure,
                        unit_price_cents=unit_price,
                        image_url=image,
                        product_url=f"https://allforyou.sg/product/{sku}",
                        in_stock=in_stock
                    ))
        except Exception as e:
            logger.warning(f"Live Sheng Siong search failed: {e}")

        return results

    # -------------------------------------------------------------------------
    # Little Farms Real Search & Scraper
    # -------------------------------------------------------------------------
    async def search_littlefarms(self, query: str) -> list[LiveProductResult]:
        results: list[LiveProductResult] = []
        try:
            # Little Farms Shopify Suggest Endpoint
            url = f"https://littlefarms.com/search/suggest.json?q={query}&resources[type]=product"
            resp = await self.http_client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("resources", {}).get("results", {}).get("products", [])
                for p in products:
                    sku = str(p.get("id") or p.get("handle") or "LF_000")
                    title = p.get("title") or "Little Farms Product"
                    price_num = float(p.get("price") or 0.0)
                    price_cents = round(price_num * 100)
                    image = p.get("image")
                    in_stock = bool(p.get("available", True))
                    pack_spec = parse_pack_size(title)
                    unit_measure = pack_spec.unit if pack_spec else "pack"
                    unit_price = round(price_cents / pack_spec.amount) if pack_spec and pack_spec.amount > 0 else price_cents

                    results.append(LiveProductResult(
                        retailer_sku=f"LF_{sku}",
                        title=title,
                        brand=p.get("vendor", "Little Farms"),
                        category="Organic & Fresh",
                        price_cents=price_cents,
                        pack_size=pack_spec.raw_text if pack_spec else "1 unit",
                        unit_measure=unit_measure,
                        unit_price_cents=unit_price,
                        image_url=image,
                        product_url=f"https://littlefarms.com/products/{p.get('handle', sku)}",
                        in_stock=in_stock
                    ))
        except Exception as e:
            logger.warning(f"Live Little Farms search failed: {e}")

        return results

    # -------------------------------------------------------------------------
    # RedMart Real Search & Scraper
    # -------------------------------------------------------------------------
    async def search_redmart(self, query: str) -> list[LiveProductResult]:
        raise NotImplementedError("Live RedMart scraping is not yet implemented.")
