"""
Journal service for managing trade journal entries and tags.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json

from app.models.journal import JournalEntry, TradeTag
from app.models.trade import Trade


class JournalService:
    """Service for journal entry and tag management."""
    
    def __init__(self, db: Session):
        """
        Initialize journal service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_or_update_journal_entry(
        self,
        user_id: int,
        trade_id: int,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        pre_trade_analysis: Optional[str] = None,
        post_trade_analysis: Optional[str] = None,
        emotional_state: Optional[str] = None,
        mistakes: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        screenshot_urls: Optional[List[str]] = None
    ) -> JournalEntry:
        """
        Create or update a journal entry for a trade.
        
        Args:
            user_id: User ID
            trade_id: Trade ID
            title: Entry title
            notes: General notes
            pre_trade_analysis: Analysis before trade
            post_trade_analysis: Analysis after trade
            emotional_state: Emotional state during trade
            mistakes: Mistakes made
            lessons_learned: Lessons learned
            screenshot_urls: List of screenshot URLs
            
        Returns:
            JournalEntry
            
        Raises:
            HTTPException: If trade not found or unauthorized
        """
        # Verify trade belongs to user
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
        
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade not found"
            )
        
        # Check if journal entry already exists
        journal_entry = self.db.query(JournalEntry).filter(
            JournalEntry.trade_id == trade_id
        ).first()
        
        # Convert screenshot URLs to JSON string
        screenshots_json = None
        if screenshot_urls:
            screenshots_json = json.dumps(screenshot_urls)
        
        if journal_entry:
            # Update existing entry
            if title is not None:
                journal_entry.title = title
            if notes is not None:
                journal_entry.notes = notes
            if pre_trade_analysis is not None:
                journal_entry.pre_trade_analysis = pre_trade_analysis
            if post_trade_analysis is not None:
                journal_entry.post_trade_analysis = post_trade_analysis
            if emotional_state is not None:
                journal_entry.emotional_state = emotional_state
            if mistakes is not None:
                journal_entry.mistakes = mistakes
            if lessons_learned is not None:
                journal_entry.lessons_learned = lessons_learned
            if screenshots_json is not None:
                journal_entry.screenshot_urls = screenshots_json
        else:
            # Create new entry
            journal_entry = JournalEntry(
                user_id=user_id,
                trade_id=trade_id,
                title=title,
                notes=notes,
                pre_trade_analysis=pre_trade_analysis,
                post_trade_analysis=post_trade_analysis,
                emotional_state=emotional_state,
                mistakes=mistakes,
                lessons_learned=lessons_learned,
                screenshot_urls=screenshots_json
            )
            self.db.add(journal_entry)
        
        self.db.commit()
        self.db.refresh(journal_entry)
        
        return journal_entry
    
    def get_journal_entry(self, trade_id: int, user_id: int) -> Optional[JournalEntry]:
        """
        Get journal entry for a trade.
        
        Args:
            trade_id: Trade ID
            user_id: User ID (for authorization)
            
        Returns:
            JournalEntry if found, None otherwise
        """
        return self.db.query(JournalEntry).join(Trade).filter(
            JournalEntry.trade_id == trade_id,
            Trade.user_id == user_id
        ).first()
    
    def create_tag(
        self,
        user_id: int,
        name: str,
        color: Optional[str] = None,
        category: Optional[str] = None
    ) -> TradeTag:
        """
        Create a new trade tag.
        
        Args:
            user_id: User ID
            name: Tag name
            color: Hex color code (optional)
            category: Tag category (optional)
            
        Returns:
            Created TradeTag
        """
        # Check if tag already exists
        existing = self.db.query(TradeTag).filter(
            TradeTag.user_id == user_id,
            TradeTag.name == name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag already exists"
            )
        
        tag = TradeTag(
            user_id=user_id,
            name=name,
            color=color,
            category=category
        )
        
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        
        return tag
    
    def get_user_tags(self, user_id: int) -> List[TradeTag]:
        """
        Get all tags for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of tags
        """
        return self.db.query(TradeTag).filter(
            TradeTag.user_id == user_id
        ).all()
    
    def add_tag_to_trade(self, trade_id: int, tag_id: int, user_id: int) -> bool:
        """
        Add a tag to a trade.
        
        Args:
            trade_id: Trade ID
            tag_id: Tag ID
            user_id: User ID (for authorization)
            
        Returns:
            True if successful
            
        Raises:
            HTTPException: If trade or tag not found or unauthorized
        """
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
        
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade not found"
            )
        
        tag = self.db.query(TradeTag).filter(
            TradeTag.id == tag_id,
            TradeTag.user_id == user_id
        ).first()
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Check if tag already added
        if tag not in trade.tags:
            trade.tags.append(tag)
            self.db.commit()
        
        return True
    
    def remove_tag_from_trade(self, trade_id: int, tag_id: int, user_id: int) -> bool:
        """
        Remove a tag from a trade.
        
        Args:
            trade_id: Trade ID
            tag_id: Tag ID
            user_id: User ID (for authorization)
            
        Returns:
            True if successful
        """
        trade = self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
        
        if not trade:
            return False
        
        tag = self.db.query(TradeTag).filter(
            TradeTag.id == tag_id,
            TradeTag.user_id == user_id
        ).first()
        
        if not tag:
            return False
        
        if tag in trade.tags:
            trade.tags.remove(tag)
            self.db.commit()
        
        return True
