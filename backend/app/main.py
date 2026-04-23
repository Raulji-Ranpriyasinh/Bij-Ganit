"""FastAPI entrypoint (Sprint 0.1).

Wires together config, CORS and the v1 router.  The `/api/ping` health check
matches the contract in the task spec (`{"success": "ok"}`) — not the
Laravel reference's `crater-self-hosted` string — so the frontend and CI can
rely on a stable response.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.config import settings

app = FastAPI(title="Bij-Ganit API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/ping", tags=["health"])
async def ping() -> dict[str, str]:
    return {"success": "ok"}


app.include_router(api_v1_router, prefix="/api")
