"""
MT5 Account database model.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class MT5Account(Base):
    """MT5 trading account model with encrypted credentials."""
    
    __tablename__ = "mt5_accounts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Reference
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Account Details
    account_number = Column(String(100), nullable=False, index=True)
    account_name = Column(String(255), nullable=True)  # User-defined nickname
    broker_name = Column(String(255), nullable=False)
    server_name = Column(String(255), nullable=False)
    
    # Encrypted Credentials (password encrypted at rest)
    encrypted_password = Column(Text, nullable=False)
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_connection_error = Column(Text, nullable=True)
    
    # Account Metadata
    account_currency = Column(String(10), nullable=True)
    account_leverage = Column(Integer, nullable=True)
    account_balance = Column(String(50), nullable=True)  # Store as string to avoid precision issues
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mt5_accounts")
    trades = relationship("Trade", back_populates="mt5_account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MT5Account(id={self.id}, account={self.account_number}, broker='{self.broker_name}')>"
