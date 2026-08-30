import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from domain.models.core import ShoppingList, ShoppingListItem
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

from apps.api.core import ADAPTER_MAP, DATABASE_URL, engine, get_session
from apps.api.routers import (
    approvals_router,
    comparison_runs_router,
    execute_live_retailer_worker,
    orders_router,
    retailer_sessions_router,
    shopping_lists_router,
)

__all__ = ["ADAPTER_MAP", "app", "execute_live_retailer_worker", "get_session"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DATABASE_URL.startswith("sqlite"):
        SQLModel.metadata.create_all(engine)
        # Ensure default shopping list exists
        with Session(engine) as session:
            lists = session.exec(select(ShoppingList)).all()
            if not lists:
                default_list = ShoppingList(
                    name="Weekly Groceries",
                    description="Standard Singapore weekly grocery essentials",
                    version=1,
                    is_active=True,
                )
                session.add(default_list)
                session.commit()
                session.refresh(default_list)

                default_items = [
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Milk",
                        category="Dairy & Chilled",
                        desired_quantity=2.0,
                        unit_measure="L",
                        must_have=True,
                        preferred_brands=["Meiji"],
                        exclusions=["soy", "almond", "powder"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Eggs",
                        category="Eggs",
                        desired_quantity=10.0,
                        unit_measure="pieces",
                        must_have=True,
                        preferred_brands=["Dasoon", "Chew's", "Honest Eggs Co."],
                        exclusions=["salted", "century"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Fresh Lemons",
                        category="Fresh Produce",
                        desired_quantity=3.0,
                        unit_measure="pieces",
                        must_have=True,
                        preferred_brands=[],
                        exclusions=["dishwash", "cleaner", "detergent", "tea", "soap"],
                    ),
                    ShoppingListItem(
                        shopping_list_id=default_list.id,
                        name="Sparkling Water",
                        category="Beverages",
                        desired_quantity=1.0,
                        unit_measure="L",
                        must_have=False,
                        preferred_brands=["San Pellegrino"],
                        exclusions=["flavored", "sweetened"],
                    ),
                ]
                for item in default_items:
                    session.add(item)
                session.commit()

    yield


app = FastAPI(
    title="Multi-Agent AI Grocery Assistant Control Plane",
    version="2.0.0",
    description="Singapore Multi-Store Grocery Comparison, Rebalancing & Ordering Platform",
    lifespan=lifespan,
)

_cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Idempotency-Key"],
)

# Include Modular Routers
app.include_router(shopping_lists_router)
app.include_router(comparison_runs_router)
app.include_router(retailer_sessions_router)
app.include_router(approvals_router)
app.include_router(orders_router)


@app.get("/health", tags=["System"])
def health_check(session: Session = Depends(get_session)):
    live_enabled = os.getenv("LIVE_PURCHASE_ENABLED", "false").lower() == "true"
    db_status = "healthy"
    try:
        session.exec(select(ShoppingList).limit(1)).first()
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "live_purchase_enabled": live_enabled,
        "live_purchasing_enabled": live_enabled,
    }
