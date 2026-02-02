"""
MT5 Account database model for storing broker credentials.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MT5Account(Base):
    """MT5 Account credentials for auto-sync."""
    
    __tablename__ = "mt5_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # MT5 Credentials (encrypted)
    mt5_login = Column(String(255), nullable=False)  # Account number
    mt5_password_encrypted = Column(Text, nullable=False)  # Encrypted password
    mt5_server = Column(String(255), nullable=False)  # Broker server name
    
    # Sync settings
    is_active = Column(Boolean, default=True, nullable=False)
    sync_interval_minutes = Column(Integer, default=5, nullable=False)  # How often to sync
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)  # 'success', 'error', 'pending'
    last_sync_message = Column(Text, nullable=True)  # Error message if failed
    last_trade_time = Column(DateTime(timezone=True), nullable=True)  # Last synced trade time
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationship
    user = relationship("User", backref="mt5_account")
    
    def __repr__(self):
        return f"<MT5Account(user_id={self.user_id}, login={self.mt5_login}, server={self.mt5_server})>"
