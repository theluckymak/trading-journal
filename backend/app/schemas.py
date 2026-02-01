"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# User Schemas
class UserRole(str, Enum):
    """User role enum."""
    USER = "user"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters with uppercase, lowercase, digit, and special character"
    )
    full_name: Optional[str] = Field(None, max_length=100, pattern="^[a-zA-Z0-9\\s\\-\\.]+$")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for user profile update."""
    full_name: Optional[str] = Field(None, max_length=100, pattern="^[a-zA-Z0-9\\s\\-\\.]+$")
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


# MT5 Account Schemas
class MT5AccountCreate(BaseModel):
    """Schema for adding MT5 account."""
    account_number: str
    password: str
    broker_name: str
    server_name: str
    account_name: Optional[str] = None


class MT5AccountResponse(BaseModel):
    """Schema for MT5 account response."""
    id: int
    account_number: str
    account_name: Optional[str]
    broker_name: str
    server_name: str
    is_active: bool
    is_connected: bool
    last_sync_at: Optional[datetime]
    account_currency: Optional[str]
    account_leverage: Optional[int]
    account_balance: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Trade Schemas
class TradeType(str, Enum):
    """Trade type enum."""
    BUY = "buy"
    SELL = "sell"


class TradeSource(str, Enum):
    """Trade source enum."""
    MT5_AUTO = "mt5_auto"
    MANUAL = "manual"


class TradeCreate(BaseModel):
    """Schema for creating manual trade."""
    symbol: str = Field(..., min_length=1, max_length=20, pattern="^[A-Z0-9]+$", description="Trading symbol (uppercase alphanumeric)")
    trade_type: TradeType
    volume: float = Field(..., gt=0, le=1000000, description="Position size must be positive and reasonable")
    open_price: float = Field(..., gt=0, le=1000000)
    open_time: datetime
    close_price: Optional[float] = Field(None, gt=0, le=1000000)
    close_time: Optional[datetime] = None
    stop_loss: Optional[float] = Field(None, gt=0)
    take_profit: Optional[float] = Field(None, gt=0)
    profit: Optional[float] = Field(None, ge=-1000000, le=1000000)
    commission: float = Field(0.0, ge=-10000, le=0)
    swap: float = Field(0.0, ge=-10000, le=10000)
    is_closed: Optional[bool] = False


class TradeUpdate(BaseModel):
    """Schema for updating trade."""
    symbol: Optional[str] = None
    trade_type: Optional[TradeType] = None
    volume: Optional[float] = Field(None, gt=0)
    open_price: Optional[float] = Field(None, gt=0)
    open_time: Optional[datetime] = None
    close_price: Optional[float] = None
    close_time: Optional[datetime] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: Optional[float] = None
    commission: Optional[float] = None
    swap: Optional[float] = None
    is_closed: Optional[bool] = None


class TradeResponse(BaseModel):
    """Schema for trade response."""
    id: int
    symbol: str
    trade_type: str
    trade_source: str
    volume: float
    open_price: float
    close_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    open_time: datetime
    close_time: Optional[datetime]
    profit: Optional[float]
    commission: float
    swap: float
    net_profit: Optional[float]
    is_closed: bool
    mt5_ticket: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Journal Schemas
class JournalEntryCreate(BaseModel):
    """Schema for creating/updating journal entry."""
    title: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=10000)
    pre_trade_analysis: Optional[str] = Field(None, max_length=10000)
    post_trade_analysis: Optional[str] = Field(None, max_length=10000)
    emotional_state: Optional[str] = Field(None, max_length=500)
    mistakes: Optional[str] = Field(None, max_length=5000)
    lessons_learned: Optional[str] = Field(None, max_length=5000)
    screenshot_urls: Optional[List[str]] = Field(None, max_items=10)


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response."""
    id: int
    trade_id: int
    title: Optional[str]
    notes: Optional[str]
    pre_trade_analysis: Optional[str]
    post_trade_analysis: Optional[str]
    emotional_state: Optional[str]
    mistakes: Optional[str]
    lessons_learned: Optional[str]
    screenshot_urls: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TradeTagCreate(BaseModel):
    """Schema for creating trade tag."""
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = None


class TradeTagResponse(BaseModel):
    """Schema for trade tag response."""
    id: int
    name: str
    color: Optional[str]
    category: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Analytics Schemas
class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    average_win: float
    average_loss: float
    profit_factor: float
    expectancy: float
    largest_win: float
    largest_loss: float
