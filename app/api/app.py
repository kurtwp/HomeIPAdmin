"""FastAPI application creation and mounting onto NiceGUI."""

from fastapi import FastAPI
from nicegui import app as nicegui_app

from app.api.dashboard import router as dashboard_router
from app.api.devices import router as devices_router
from app.api.docs_api import router as docs_router
from app.api.ip_addresses import router as ips_router
from app.api.monitors import router as monitors_router
from app.api.networks import router as networks_router
from app.api.search import router as search_router
from app.api.tags import router as tags_router

api = FastAPI(
    title="Home Lab Manager API",
    description="REST API for the Home Lab Manager — IPAM, device inventory, monitoring, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Include routers ---
api.include_router(dashboard_router)
api.include_router(networks_router)
api.include_router(ips_router)
api.include_router(devices_router)
api.include_router(tags_router)
api.include_router(monitors_router)
api.include_router(docs_router)
api.include_router(search_router)


@api.get("/health", tags=["System"])
def health_check():
    """Simple health-check endpoint (no auth required)."""
    return {"status": "ok", "service": "home-lab-manager"}


# Mount onto the NiceGUI Starlette app so both UI and API are served.
nicegui_app.mount("/api", api)
