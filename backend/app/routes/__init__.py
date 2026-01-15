"""
Routes package initialization.
"""
from app.routes.auth import router as auth_router
from app.routes.mt5 import router as mt5_router
from app.routes.trades import router as trades_router
from app.routes.journal import router as journal_router

__all__ = [
    "auth_router",
    "mt5_router",
    "trades_router",
    "journal_router",
]
