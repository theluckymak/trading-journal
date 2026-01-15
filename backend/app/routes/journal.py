"""
Journal routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import (
    JournalEntryCreate,
    JournalEntryResponse,
    TradeTagCreate,
    TradeTagResponse
)
from app.services.journal_service import JournalService
from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post("/entries/{trade_id}", response_model=JournalEntryResponse)
async def create_or_update_journal_entry(
    trade_id: int,
    entry_data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update a journal entry for a trade."""
    journal_service = JournalService(db)
    
    entry = journal_service.create_or_update_journal_entry(
        user_id=current_user.id,
        trade_id=trade_id,
        title=entry_data.title,
        notes=entry_data.notes,
        pre_trade_analysis=entry_data.pre_trade_analysis,
        post_trade_analysis=entry_data.post_trade_analysis,
        emotional_state=entry_data.emotional_state,
        mistakes=entry_data.mistakes,
        lessons_learned=entry_data.lessons_learned,
        screenshot_urls=entry_data.screenshot_urls
    )
    
    return entry


@router.get("/entries/{trade_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get journal entry for a trade."""
    journal_service = JournalService(db)
    entry = journal_service.get_journal_entry(trade_id, current_user.id)
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal entry not found"
        )
    
    return entry


@router.post("/tags", response_model=TradeTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TradeTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trade tag."""
    journal_service = JournalService(db)
    
    tag = journal_service.create_tag(
        user_id=current_user.id,
        name=tag_data.name,
        color=tag_data.color,
        category=tag_data.category
    )
    
    return tag


@router.get("/tags", response_model=List[TradeTagResponse])
async def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tags for current user."""
    journal_service = JournalService(db)
    tags = journal_service.get_user_tags(current_user.id)
    return tags


@router.post("/trades/{trade_id}/tags/{tag_id}")
async def add_tag_to_trade(
    trade_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a tag to a trade."""
    journal_service = JournalService(db)
    
    journal_service.add_tag_to_trade(trade_id, tag_id, current_user.id)
    
    return {"message": "Tag added to trade successfully"}


@router.delete("/trades/{trade_id}/tags/{tag_id}")
async def remove_tag_from_trade(
    trade_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a tag from a trade."""
    journal_service = JournalService(db)
    
    success = journal_service.remove_tag_from_trade(trade_id, tag_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade or tag not found"
        )
    
    return {"message": "Tag removed from trade successfully"}
