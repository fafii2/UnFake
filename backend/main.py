"""
UnFake Backend — FastAPI Application Entry Point

Start the server:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.router import router as api_router

app = FastAPI(
    title="UnFake API",
    description="AI-assisted misinformation verification backend",
    version="0.1.0",
)

# CORS middleware — allows the browser extension to reach the backend.
# In development, we also allow localhost origins for testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# Mount the API router under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"service": "unfake-api", "version": "0.1.0", "status": "running"}
