"""Routers de FastAPI."""
from . import wuzapi_router
from . import chatwoot_router

__all__ = [
    "wuzapi_router",
    "chatwoot_router"
]