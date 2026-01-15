"""
MT5 account routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import MT5AccountCreate, MT5AccountResponse
from app.services.mt5_service import MT5Service
from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/mt5", tags=["MT5 Accounts"])


@router.post("/accounts", response_model=MT5AccountResponse, status_code=status.HTTP_201_CREATED)
async def add_mt5_account(
    account_data: MT5AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new MT5 account."""
    mt5_service = MT5Service(db)
    
    account = mt5_service.add_mt5_account(
        user_id=current_user.id,
        account_number=account_data.account_number,
        password=account_data.password,
        broker_name=account_data.broker_name,
        server_name=account_data.server_name,
        account_name=account_data.account_name
    )
    
    return account


@router.get("/accounts", response_model=List[MT5AccountResponse])
async def get_mt5_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all MT5 accounts for current user."""
    mt5_service = MT5Service(db)
    accounts = mt5_service.get_user_mt5_accounts(current_user.id)
    return accounts


@router.post("/accounts/{account_id}/sync")
async def sync_mt5_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Synchronize trades from MT5 account."""
    mt5_service = MT5Service(db)
    
    # Verify account belongs to user
    accounts = mt5_service.get_user_mt5_accounts(current_user.id)
    if not any(acc.id == account_id for acc in accounts):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MT5 account not found"
        )
    
    new_trades = mt5_service.sync_trades(account_id)
    
    return {
        "message": f"Synchronized {new_trades} new trade(s)",
        "new_trades": new_trades
    }


@router.delete("/accounts/{account_id}")
async def delete_mt5_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an MT5 account."""
    mt5_service = MT5Service(db)
    
    success = mt5_service.delete_mt5_account(account_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MT5 account not found"
        )
    
    return {"message": "MT5 account deleted successfully"}
