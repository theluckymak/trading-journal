"""
Models package initialization.
Import all models here to ensure they're registered with SQLAlchemy.
"""
from app.models.user import User, UserRole
from app.models.auth import RefreshToken, PasswordResetToken
from app.models.mt5_account import MT5Account
from app.models.trade import Trade, TradeType, TradeSource
from app.models.journal import JournalEntry, TradeTag, trade_tag_associations

__all__ = [
    "User",
    "UserRole",
    "RefreshToken",
    "PasswordResetToken",
    "MT5Account",
    "Trade",
    "TradeType",
    "TradeSource",
    "JournalEntry",
    "TradeTag",
    "trade_tag_associations",
]
