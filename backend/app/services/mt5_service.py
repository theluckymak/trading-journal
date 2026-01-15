"""
MT5 integration service for connecting and syncing trading accounts.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import MetaTrader5 as mt5

from app.models.mt5_account import MT5Account
from app.models.trade import Trade, TradeType, TradeSource
from app.services.encryption_service import encryption_service


class MT5Service:
    """Service for MT5 account management and trade synchronization."""
    
    def __init__(self, db: Session):
        """
        Initialize MT5 service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def add_mt5_account(
        self,
        user_id: int,
        account_number: str,
        password: str,
        broker_name: str,
        server_name: str,
        account_name: Optional[str] = None
    ) -> MT5Account:
        """
        Add a new MT5 account for a user.
        
        Args:
            user_id: User ID
            account_number: MT5 account number
            password: MT5 account password (will be encrypted)
            broker_name: Broker name
            server_name: MT5 server name
            account_name: Optional nickname for the account
            
        Returns:
            Created MT5Account
            
        Raises:
            HTTPException: If account already exists
        """
        # Check if account already exists
        existing = self.db.query(MT5Account).filter(
            MT5Account.user_id == user_id,
            MT5Account.account_number == account_number,
            MT5Account.server_name == server_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MT5 account already added"
            )
        
        # Encrypt password
        encrypted_password = encryption_service.encrypt(password)
        
        # Create account record
        mt5_account = MT5Account(
            user_id=user_id,
            account_number=account_number,
            account_name=account_name or f"{broker_name} - {account_number}",
            broker_name=broker_name,
            server_name=server_name,
            encrypted_password=encrypted_password
        )
        
        self.db.add(mt5_account)
        self.db.commit()
        self.db.refresh(mt5_account)
        
        # Try to connect and verify account (non-blocking)
        try:
            self._test_connection(mt5_account)
        except Exception as e:
            # Connection test failed, but still return the account
            mt5_account.is_connected = False
            mt5_account.last_connection_error = f"Connection test failed: {str(e)}"
            self.db.commit()
        
        return mt5_account
    
    def _test_connection(self, mt5_account: MT5Account) -> bool:
        """
        Test connection to MT5 account.
        
        Args:
            mt5_account: MT5Account to test
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize MT5
            if not mt5.initialize():
                error_msg = "MT5 terminal not found. Please ensure MetaTrader 5 is installed and running."
                mt5_account.is_connected = False
                mt5_account.last_connection_error = error_msg
                self.db.commit()
                return False
            
            # Decrypt password
            password = encryption_service.decrypt(mt5_account.encrypted_password)
            if not password:
                mt5_account.is_connected = False
                mt5_account.last_connection_error = "Failed to decrypt password"
                self.db.commit()
                return False
            
            # Login
            authorized = mt5.login(
                login=int(mt5_account.account_number),
                password=password,
                server=mt5_account.server_name
            )
            
            if not authorized:
                error = mt5.last_error()
                mt5_account.is_connected = False
                mt5_account.last_connection_error = f"Login failed: {error}"
                self.db.commit()
                mt5.shutdown()
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info:
                mt5_account.account_currency = account_info.currency
                mt5_account.account_leverage = account_info.leverage
                mt5_account.account_balance = str(account_info.balance)
            
            mt5_account.is_connected = True
            mt5_account.last_connection_error = None
            self.db.commit()
            
            mt5.shutdown()
            return True
            
        except Exception as e:
            mt5_account.is_connected = False
            mt5_account.last_connection_error = str(e)
            self.db.commit()
            return False
    
    def sync_trades(self, mt5_account_id: int) -> int:
        """
        Synchronize trades from MT5 account.
        
        Args:
            mt5_account_id: MT5Account ID
            
        Returns:
            Number of new trades imported
            
        Raises:
            HTTPException: If account not found or connection fails
        """
        mt5_account = self.db.query(MT5Account).filter(
            MT5Account.id == mt5_account_id
        ).first()
        
        if not mt5_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MT5 account not found"
            )
        
        try:
            # Initialize and login
            if not mt5.initialize():
                error_msg = "MetaTrader 5 terminal is not running or not installed. Please ensure MT5 is installed and running, then try again."
                mt5_account.last_connection_error = error_msg
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )
            
            password = encryption_service.decrypt(mt5_account.encrypted_password)
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to decrypt password"
                )
            
            authorized = mt5.login(
                login=int(mt5_account.account_number),
                password=password,
                server=mt5_account.server_name
            )
            
            if not authorized:
                error = mt5.last_error()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"MT5 login failed: {error}"
                )
            
            # Get all closed deals (history)
            from_date = datetime(2020, 1, 1)  # Adjust as needed
            to_date = datetime.utcnow()
            
            deals = mt5.history_deals_get(from_date, to_date)
            
            if deals is None:
                mt5.shutdown()
                return 0
            
            # Process deals into trades
            trades_dict: Dict[int, Dict[str, Any]] = {}
            
            for deal in deals:
                ticket = deal.position_id
                if ticket == 0:
                    continue  # Skip balance operations
                
                if ticket not in trades_dict:
                    trades_dict[ticket] = {
                        'ticket': ticket,
                        'symbol': deal.symbol,
                        'volume': deal.volume,
                        'open_time': None,
                        'close_time': None,
                        'open_price': None,
                        'close_price': None,
                        'type': None,
                        'profit': 0.0,
                        'commission': 0.0,
                        'swap': 0.0,
                        'sl': 0.0,
                        'tp': 0.0
                    }
                
                trade_data = trades_dict[ticket]
                
                # Entry deal
                if deal.entry == mt5.DEAL_ENTRY_IN:
                    trade_data['open_time'] = datetime.fromtimestamp(deal.time)
                    trade_data['open_price'] = deal.price
                    trade_data['type'] = TradeType.BUY if deal.type == mt5.DEAL_TYPE_BUY else TradeType.SELL
                    trade_data['sl'] = deal.sl if hasattr(deal, 'sl') else 0.0
                    trade_data['tp'] = deal.tp if hasattr(deal, 'tp') else 0.0
                
                # Exit deal
                elif deal.entry == mt5.DEAL_ENTRY_OUT:
                    trade_data['close_time'] = datetime.fromtimestamp(deal.time)
                    trade_data['close_price'] = deal.price
                
                # Accumulate financials
                trade_data['profit'] += deal.profit
                trade_data['commission'] += deal.commission
                trade_data['swap'] += deal.swap
            
            # Save trades to database
            new_trades_count = 0
            
            for ticket, trade_data in trades_dict.items():
                # Check if trade already exists
                existing = self.db.query(Trade).filter(
                    Trade.mt5_account_id == mt5_account_id,
                    Trade.mt5_ticket == str(ticket)
                ).first()
                
                if existing:
                    continue
                
                # Only save completed trades
                if not trade_data['close_time']:
                    continue
                
                # Calculate net profit
                net_profit = (
                    trade_data['profit'] +
                    trade_data['commission'] +
                    trade_data['swap']
                )
                
                # Create trade record
                trade = Trade(
                    user_id=mt5_account.user_id,
                    mt5_account_id=mt5_account_id,
                    mt5_ticket=str(ticket),
                    trade_source=TradeSource.MT5_AUTO,
                    symbol=trade_data['symbol'],
                    trade_type=trade_data['type'],
                    volume=trade_data['volume'],
                    open_price=trade_data['open_price'],
                    close_price=trade_data['close_price'],
                    stop_loss=trade_data['sl'] if trade_data['sl'] > 0 else None,
                    take_profit=trade_data['tp'] if trade_data['tp'] > 0 else None,
                    open_time=trade_data['open_time'],
                    close_time=trade_data['close_time'],
                    profit=trade_data['profit'],
                    commission=trade_data['commission'],
                    swap=trade_data['swap'],
                    net_profit=net_profit,
                    is_closed=True
                )
                
                self.db.add(trade)
                new_trades_count += 1
            
            # Update last sync time
            mt5_account.last_sync_at = datetime.utcnow()
            mt5_account.is_connected = True
            mt5_account.last_connection_error = None
            
            self.db.commit()
            mt5.shutdown()
            
            return new_trades_count
            
        except Exception as e:
            mt5.shutdown()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Trade sync failed: {str(e)}"
            )
    
    def get_user_mt5_accounts(self, user_id: int) -> List[MT5Account]:
        """
        Get all MT5 accounts for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of MT5 accounts
        """
        return self.db.query(MT5Account).filter(
            MT5Account.user_id == user_id
        ).all()
    
    def delete_mt5_account(self, mt5_account_id: int, user_id: int) -> bool:
        """
        Delete an MT5 account.
        
        Args:
            mt5_account_id: MT5Account ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        mt5_account = self.db.query(MT5Account).filter(
            MT5Account.id == mt5_account_id,
            MT5Account.user_id == user_id
        ).first()
        
        if not mt5_account:
            return False
        
        self.db.delete(mt5_account)
        self.db.commit()
        
        return True
