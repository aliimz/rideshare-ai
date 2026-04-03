"""
RideShare AI — FastAPI application entry point.

Run from the rideshare-ai/ directory:
    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="RideShare AI",
    description="AI-powered ride-sharing demo backend for Lahore",
    version="1.0.0",
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
# Mount API router  (all routes are prefixed with /api inside the router)
# ---------------------------------------------------------------------------
app.include_router(router)


@app.get("/", summary="Health check")
def root() -> dict:
    return {"status": "ok", "message": "RideShare AI backend is running."}


# ---------------------------------------------------------------------------
# Uvicorn entry point — run directly: python -m backend.main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
