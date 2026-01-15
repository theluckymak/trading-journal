"""
Journal and tagging database models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


# Association table for many-to-many relationship between trades and tags
trade_tag_associations = Table(
    'trade_tag_associations',
    Base.metadata,
    Column('trade_id', Integer, ForeignKey('trades.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('trade_tags.id', ondelete='CASCADE'), primary_key=True)
)


class TradeTag(Base):
    """Tag model for categorizing trades (strategy, session, market condition, etc.)."""
    
    __tablename__ = "trade_tags"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Reference
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Tag Details
    name = Column(String(100), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color code (e.g., #FF5733)
    category = Column(String(50), nullable=True)  # e.g., "strategy", "session", "market"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    trades = relationship("Trade", secondary=trade_tag_associations, back_populates="tags")
    
    def __repr__(self):
        return f"<TradeTag(id={self.id}, name='{self.name}', category='{self.category}')>"


class JournalEntry(Base):
    """Journal entry model for detailed trade notes and analysis."""
    
    __tablename__ = "journal_entries"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Entry Content
    title = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    pre_trade_analysis = Column(Text, nullable=True)
    post_trade_analysis = Column(Text, nullable=True)
    
    # Trade Psychology
    emotional_state = Column(String(50), nullable=True)  # e.g., "confident", "fearful", "neutral"
    mistakes = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    
    # Media
    screenshot_urls = Column(Text, nullable=True)  # JSON array stored as text
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="journal_entries")
    trade = relationship("Trade", back_populates="journal_entry")
    
    def __repr__(self):
        return f"<JournalEntry(id={self.id}, trade_id={self.trade_id})>"
