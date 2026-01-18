"""
Trade service for managing trades and analytics.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status

from app.models.trade import Trade, TradeType, TradeSource
from app.models.journal import JournalEntry, TradeTag


class TradeService:
    """Service for trade management and analytics."""
    
    def __init__(self, db: Session):
        """
        Initialize trade service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_manual_trade(
        self,
        user_id: int,
        symbol: str,
        trade_type: TradeType,
        volume: float,
        open_price: float,
        open_time: datetime,
        close_price: Optional[float] = None,
        close_time: Optional[datetime] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        profit: Optional[float] = None,
        commission: float = 0.0,
        swap: float = 0.0,
        is_closed: Optional[bool] = None
    ) -> Trade:
        """
        Create a manual trade entry.
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            trade_type: Buy or Sell
            volume: Position size
            open_price: Entry price
            open_time: Entry time
            close_price: Exit price (optional)
            close_time: Exit time (optional)
            stop_loss: Stop loss level (optional)
            take_profit: Take profit level (optional)
            profit: Profit/loss amount (optional)
            commission: Commission amount
            swap: Swap amount
            
        Returns:
            Created Trade
        """
        # Calculate profit if close_price is provided but profit isn't
        if profit is None and close_price is not None:
            # Calculate profit based on trade type
            if trade_type == TradeType.BUY:
                profit = (close_price - open_price) * volume
            else:  # SELL
                profit = (open_price - close_price) * volume
        
        # Calculate net profit
        net_profit = None
        if profit is not None:
            net_profit = profit - commission - swap
        
        # Determine if trade is closed
        # If user explicitly sets is_closed, use that value
        # Otherwise, auto-detect based on close_price and close_time
        if is_closed is None:
            is_closed = close_price is not None and close_time is not None
        else:
            is_closed = is_closed
        
        trade = Trade(
            user_id=user_id,
            trade_source=TradeSource.MANUAL,
            symbol=symbol,
            trade_type=trade_type,
            volume=volume,
            open_price=open_price,
            close_price=close_price,
            open_time=open_time,
            close_time=close_time,
            stop_loss=stop_loss,
            take_profit=take_profit,
            profit=profit,
            commission=commission,
            swap=swap,
            net_profit=net_profit,
            is_closed=is_closed
        )
        
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        
        return trade
    
    def get_user_trades(
        self,
        user_id: int,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_closed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """
        Get trades for a user with optional filters.
        
        Args:
            user_id: User ID
            symbol: Filter by symbol (optional)
            start_date: Filter trades after this date (optional)
            end_date: Filter trades before this date (optional)
            is_closed: Filter by closed status (optional)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of trades
        """
        query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        if start_date:
            query = query.filter(Trade.open_time >= start_date)
        
        if end_date:
            query = query.filter(Trade.open_time <= end_date)
        
        if is_closed is not None:
            query = query.filter(Trade.is_closed == is_closed)
        
        query = query.order_by(Trade.open_time.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_trade_by_id(self, trade_id: int, user_id: int) -> Optional[Trade]:
        """
        Get a specific trade.
        
        Args:
            trade_id: Trade ID
            user_id: User ID (for authorization)
            
        Returns:
            Trade if found, None otherwise
        """
        return self.db.query(Trade).filter(
            Trade.id == trade_id,
            Trade.user_id == user_id
        ).first()
    
    def update_trade(
        self,
        trade_id: int,
        user_id: int,
        **kwargs
    ) -> Optional[Trade]:
        """
        Update a trade.
        
        Args:
            trade_id: Trade ID
            user_id: User ID (for authorization)
            **kwargs: Fields to update
            
        Returns:
            Updated trade if found, None otherwise
        """
        trade = self.get_trade_by_id(trade_id, user_id)
        if not trade:
            return None
        
        for key, value in kwargs.items():
            if hasattr(trade, key) and value is not None:
                setattr(trade, key, value)
        
        # Recalculate profit if prices/volume updated and profit not explicitly set
        if 'profit' not in kwargs and any(k in kwargs for k in ['close_price', 'open_price', 'volume', 'trade_type']):
            if trade.close_price is not None:
                if trade.trade_type == TradeType.BUY:
                    trade.profit = (trade.close_price - trade.open_price) * trade.volume
                else:  # SELL
                    trade.profit = (trade.open_price - trade.close_price) * trade.volume
        
        # Recalculate net profit if financial fields updated
        if any(k in kwargs for k in ['profit', 'commission', 'swap']):
            if trade.profit is not None:
                trade.net_profit = trade.profit - trade.commission - trade.swap
        
        # Update is_closed status if not explicitly set
        if 'is_closed' not in kwargs:
            trade.is_closed = trade.close_price is not None and trade.close_time is not None
        
        self.db.commit()
        self.db.refresh(trade)
        
        return trade
    
    def delete_trade(self, trade_id: int, user_id: int) -> bool:
        """
        Delete a trade.
        
        Args:
            trade_id: Trade ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        trade = self.get_trade_by_id(trade_id, user_id)
        if not trade:
            return False
        
        self.db.delete(trade)
        self.db.commit()
        
        return True
    
    def calculate_analytics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate trading analytics for a user.
        
        Args:
            user_id: User ID
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Dictionary of analytics metrics
        """
        query = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.is_closed == True
        )
        
        if start_date:
            query = query.filter(Trade.close_time >= start_date)
        
        if end_date:
            query = query.filter(Trade.close_time <= end_date)
        
        trades = query.all()
        
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "total_loss": 0.0,
                "net_profit": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0
            }
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.net_profit > 0]
        losing_trades = [t for t in trades if t.net_profit <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        
        total_profit = sum(t.net_profit for t in winning_trades)
        total_loss = abs(sum(t.net_profit for t in losing_trades))
        net_profit = sum(t.net_profit for t in trades)
        
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        average_win = total_profit / win_count if win_count > 0 else 0
        average_loss = total_loss / loss_count if loss_count > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        expectancy = net_profit / total_trades if total_trades > 0 else 0
        
        largest_win = max((t.net_profit for t in trades), default=0)
        largest_loss = min((t.net_profit for t in trades), default=0)
        
        return {
            "total_trades": total_trades,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "total_loss": round(total_loss, 2),
            "net_profit": round(net_profit, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2)
        }
