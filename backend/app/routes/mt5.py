"""
MT5 Account API routes for managing broker credentials.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.mt5_account import MT5Account
from app.middleware.auth import get_current_user
from app.services.encryption_service import EncryptionService
from app.config import settings


router = APIRouter(prefix="/api/mt5", tags=["mt5"])

# VPS Secret for internal sync endpoint
VPS_SECRET = settings.ENCRYPTION_KEY  # Use same key for simplicity


# Schemas
class MT5AccountCreate(BaseModel):
    """Schema for creating/updating MT5 account."""
    mt5_login: str = Field(..., min_length=1, max_length=50, description="MT5 account number")
    mt5_password: Optional[str] = Field(None, max_length=255, description="MT5 password (optional for updates)")
    mt5_server: str = Field(..., min_length=1, max_length=255, description="Broker server name")
    sync_interval_minutes: int = Field(default=5, ge=1, le=60, description="Sync interval in minutes")
    is_active: bool = Field(default=True, description="Whether sync is active")


class MT5AccountResponse(BaseModel):
    """Schema for MT5 account response (no password)."""
    id: int
    mt5_login: str
    mt5_server: str
    is_active: bool
    sync_interval_minutes: int
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MT5AccountStatus(BaseModel):
    """Schema for MT5 sync status."""
    has_config: bool
    is_active: bool = False
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_message: Optional[str] = None
    total_trades_synced: int = 0


# Routes
@router.post("/account", response_model=MT5AccountResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_mt5_account(
    account_data: MT5AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update MT5 account credentials for auto-sync.
    Password is encrypted before storage.
    """
    encryption_service = EncryptionService()
    
    # Check if account already exists
    existing_account = db.query(MT5Account).filter(MT5Account.user_id == current_user.id).first()
    
    if existing_account:
        # Update existing
        existing_account.mt5_login = account_data.mt5_login
        existing_account.mt5_server = account_data.mt5_server
        existing_account.sync_interval_minutes = account_data.sync_interval_minutes
        existing_account.is_active = account_data.is_active
        
        # Only update password if provided
        if account_data.mt5_password:
            encrypted_password = encryption_service.encrypt(account_data.mt5_password)
            existing_account.mt5_password_encrypted = encrypted_password
        
        existing_account.last_sync_status = "pending"
        existing_account.last_sync_message = "Credentials updated, waiting for sync"
        db.commit()
        db.refresh(existing_account)
        return existing_account
    else:
        # Create new - password is required
        if not account_data.mt5_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for new accounts"
            )
        
        encrypted_password = encryption_service.encrypt(account_data.mt5_password)
        
        new_account = MT5Account(
            user_id=current_user.id,
            mt5_login=account_data.mt5_login,
            mt5_password_encrypted=encrypted_password,
            mt5_server=account_data.mt5_server,
            sync_interval_minutes=account_data.sync_interval_minutes,
            is_active=True,
            last_sync_status="pending",
            last_sync_message="Account created, waiting for first sync"
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account


@router.get("/account", response_model=MT5AccountResponse)
def get_mt5_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's MT5 account configuration."""
    account = db.query(MT5Account).filter(MT5Account.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MT5 account configured"
        )
    
    return account


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_mt5_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete MT5 account and stop auto-sync."""
    account = db.query(MT5Account).filter(MT5Account.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MT5 account configured"
        )
    
    db.delete(account)
    db.commit()
    return None


@router.post("/account/toggle", response_model=MT5AccountResponse)
def toggle_mt5_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable or disable MT5 auto-sync."""
    account = db.query(MT5Account).filter(MT5Account.user_id == current_user.id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MT5 account configured"
        )
    
    account.is_active = not account.is_active
    account.last_sync_message = "Sync enabled" if account.is_active else "Sync disabled by user"
    db.commit()
    db.refresh(account)
    return account


@router.get("/status", response_model=MT5AccountStatus)
def get_mt5_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get MT5 sync status and statistics."""
    from app.models.trade import Trade, TradeSource
    
    account = db.query(MT5Account).filter(MT5Account.user_id == current_user.id).first()
    
    if not account:
        return MT5AccountStatus(
            has_config=False,
            is_active=False,
            total_trades_synced=0
        )
    
    # Count MT5 synced trades
    mt5_trades_count = db.query(Trade).filter(
        Trade.user_id == current_user.id,
        Trade.trade_source == TradeSource.MT5_AUTO
    ).count()
    
    return MT5AccountStatus(
        has_config=True,
        is_active=account.is_active,
        last_sync_at=account.last_sync_at,
        last_sync_status=account.last_sync_status,
        last_sync_message=account.last_sync_message,
        total_trades_synced=mt5_trades_count
    )

# ============================================
# VPS Internal Sync Endpoints
# ============================================

class VPSSyncAccount(BaseModel):
    """Account data for VPS sync."""
    id: int
    user_id: int
    mt5_login: str
    mt5_password: str  # Decrypted!
    mt5_server: str
    sync_interval_minutes: int
    last_sync_at: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None


class VPSSyncStatusUpdate(BaseModel):
    """Status update from VPS."""
    account_id: int
    status: str  # 'success' or 'error'
    message: str
    last_trade_time: Optional[datetime] = None


@router.get("/vps/accounts", response_model=List[VPSSyncAccount])
def get_accounts_for_vps_sync(
    x_vps_secret: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Internal endpoint for VPS to get accounts that need syncing.
    Secured with VPS_SECRET header.
    Returns decrypted passwords.
    """
    if x_vps_secret != VPS_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VPS secret"
        )
    
    from sqlalchemy import text
    
    # Get accounts that need syncing
    accounts = db.query(MT5Account).filter(
        MT5Account.is_active == True
    ).all()
    
    encryption_service = EncryptionService()
    result = []
    
    for account in accounts:
        # Check if it's time to sync
        should_sync = False
        if account.last_sync_at is None:
            should_sync = True
        else:
            from datetime import timezone, timedelta
            now = datetime.now(timezone.utc)
            next_sync = account.last_sync_at + timedelta(minutes=account.sync_interval_minutes)
            should_sync = now >= next_sync
        
        if should_sync:
            # Decrypt password
            password = encryption_service.decrypt(account.mt5_password_encrypted)
            if password:
                result.append(VPSSyncAccount(
                    id=account.id,
                    user_id=account.user_id,
                    mt5_login=account.mt5_login,
                    mt5_password=password,
                    mt5_server=account.mt5_server,
                    sync_interval_minutes=account.sync_interval_minutes,
                    last_sync_at=account.last_sync_at,
                    last_trade_time=account.last_trade_time
                ))
    
    return result


@router.post("/vps/status")
def update_sync_status_from_vps(
    update: VPSSyncStatusUpdate,
    x_vps_secret: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Internal endpoint for VPS to update sync status.
    """
    if x_vps_secret != VPS_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VPS secret"
        )
    
    account = db.query(MT5Account).filter(MT5Account.id == update.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    from datetime import timezone
    account.last_sync_at = datetime.now(timezone.utc)
    account.last_sync_status = update.status
    account.last_sync_message = update.message
    if update.last_trade_time:
        account.last_trade_time = update.last_trade_time
    
    db.commit()
    return {"status": "updated"}