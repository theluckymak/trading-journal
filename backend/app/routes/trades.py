"""
Trade routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import TradeCreate, TradeUpdate, TradeResponse, AnalyticsResponse
from app.services.trade_service import TradeService
from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/trades", tags=["Trades"])


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_data: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a manual trade entry."""
    trade_service = TradeService(db)
    
    trade = trade_service.create_manual_trade(
        user_id=current_user.id,
        symbol=trade_data.symbol,
        trade_type=trade_data.trade_type,
        volume=trade_data.volume,
        open_price=trade_data.open_price,
        open_time=trade_data.open_time,
        close_price=trade_data.close_price,
        close_time=trade_data.close_time,
        stop_loss=trade_data.stop_loss,
        take_profit=trade_data.take_profit,
        profit=trade_data.profit,
        commission=trade_data.commission,
        swap=trade_data.swap,
        is_closed=trade_data.is_closed
    )
    
    return trade


@router.get("", response_model=List[TradeResponse])
async def get_trades(
    symbol: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_closed: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all trades for current user with optional filters."""
    trade_service = TradeService(db)
    
    trades = trade_service.get_user_trades(
        user_id=current_user.id,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        is_closed=is_closed,
        limit=limit,
        offset=offset
    )
    
    return trades


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific trade."""
    trade_service = TradeService(db)
    trade = trade_service.get_trade_by_id(trade_id, current_user.id)
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    return trade


@router.patch("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int,
    trade_data: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a trade."""
    trade_service = TradeService(db)
    
    trade = trade_service.update_trade(
        trade_id=trade_id,
        user_id=current_user.id,
        **trade_data.model_dump(exclude_unset=True)
    )
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    return trade


@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a trade."""
    trade_service = TradeService(db)
    
    success = trade_service.delete_trade(trade_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    return {"message": "Trade deleted successfully"}


@router.get("/analytics/summary", response_model=AnalyticsResponse)
async def get_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trading analytics for current user."""
    trade_service = TradeService(db)
    
    analytics = trade_service.calculate_analytics(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return analytics
