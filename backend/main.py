"""
RideShare AI — FastAPI application entry point.

Run from the rideshare-ai/ directory:
    uvicorn backend.main:app --reload --port 8080
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from backend.api.auth import router as auth_router
from backend.api.admin import router as admin_router
from backend.api.driver import router as driver_router
from backend.api.rides import router as rides_router
from backend.api.routes import router
from backend.api.websocket import ws_router
from backend.db.database import engine, AsyncSessionLocal
from backend.db.models import Base, User


# ---------------------------------------------------------------------------
# Startup: create tables + seed demo data if DB is empty
# ---------------------------------------------------------------------------


async def _init_db() -> None:
    """Create all tables (idempotent) then seed demo data if the DB is empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        already_seeded = result.scalar_one_or_none() is not None

    if not already_seeded:
        from scripts.seed import seed
        async with AsyncSessionLocal() as session:
            await seed(session)

    from scripts.seed import ensure_demo_runtime_data
    async with AsyncSessionLocal() as session:
        await ensure_demo_runtime_data(session)


async def _train_ai_models() -> None:
    """Train demand forecast and matching models on startup."""
    import asyncio
    from backend.api.routes import (
        public_demand_service as demand_svc,
        public_matching_service as match_svc,
    )
    from backend.services.ml_logging import load_match_outcomes_for_training

    X, y = await demand_svc.generate_training_data()
    if X is not None and y is not None:
        trained = await asyncio.to_thread(demand_svc.train, X, y)
        if trained:
            print(f"[AI] Demand forecast model trained on {len(y)} samples")

    outcomes = await load_match_outcomes_for_training(min_records=10)
    if outcomes:
        trained = await asyncio.to_thread(match_svc.retrain_with_outcomes, outcomes)
        if trained:
            print(f"[AI] Matching model retrained on {len(outcomes)} real outcomes")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await _init_db()
    await _train_ai_models()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RideShare AI",
    description="AI-powered ride-sharing demo backend for Lahore",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow all origins for the demo frontend
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(router)
app.include_router(ws_router)
app.include_router(auth_router, prefix="/api")
app.include_router(rides_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(driver_router, prefix="/api")


@app.get("/", summary="Health check")
def root() -> dict:
    return {"status": "ok", "message": "RideShare AI backend is running."}


# ---------------------------------------------------------------------------
# Uvicorn entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
