"""
Trade database model.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class TradeType(str, enum.Enum):
    """Trade type enumeration."""
    BUY = "buy"
    SELL = "sell"


class TradeSource(str, enum.Enum):
    """Trade source enumeration."""
    MT5_AUTO = "mt5_auto"  # Automatically imported from MT5
    MANUAL = "manual"      # Manually entered by user


class Trade(Base):
    """Trade model for storing trading history."""
    
    __tablename__ = "trades"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Reference
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Trade Identification
    mt5_ticket = Column(String(100), nullable=True, index=True)  # MT5 order ticket
    trade_source = Column(Enum(TradeSource), default=TradeSource.MANUAL, nullable=False)
    
    # Trade Details
    symbol = Column(String(50), nullable=False, index=True)
    trade_type = Column(Enum(TradeType), nullable=False)
    volume = Column(Float, nullable=False)  # Lot size
    
    # Prices
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Timestamps
    open_time = Column(DateTime(timezone=True), nullable=False, index=True)
    close_time = Column(DateTime(timezone=True), nullable=True)
    
    # Financial Results
    profit = Column(Float, nullable=True)
    commission = Column(Float, default=0.0, nullable=False)
    swap = Column(Float, default=0.0, nullable=False)
    net_profit = Column(Float, nullable=True)  # profit - commission - swap
    
    # Trade Management
    is_closed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    journal_entry = relationship("JournalEntry", back_populates="trade", uselist=False)
    tags = relationship("TradeTag", secondary="trade_tag_associations", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', type='{self.trade_type}', profit={self.net_profit})>"
