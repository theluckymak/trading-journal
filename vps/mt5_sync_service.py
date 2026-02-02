"""
MT5 Serial Sync Service for VPS
================================
This script runs on your Windows VPS and syncs trades for all users one by one.

Setup:
1. Install Python 3.8+ on your VPS
2. Install MT5 terminal on VPS
3. pip install MetaTrader5 psycopg2-binary sqlalchemy cryptography requests
4. Set your DATABASE_URL and ENCRYPTION_KEY environment variables
5. Run: python mt5_sync_service.py

The script will:
- Loop through all active MT5 accounts
- Login to each account, sync trades, then logout
- Process one account at a time (serial processing)
- Repeat every minute
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Tuple
import traceback

# Check for MetaTrader5 module
try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: MetaTrader5 module not installed.")
    print("Run: pip install MetaTrader5")
    sys.exit(1)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import base64

# ============================================
# CONFIGURATION - SET THESE ON YOUR VPS
# ============================================
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')  # Must match backend
API_URL = os.environ.get('API_URL', 'https://trading-journal-backend-production.up.railway.app')

# How often to check for accounts to sync (in seconds)
SYNC_CHECK_INTERVAL = 60

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mt5_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# ENCRYPTION SERVICE (must match backend)
# Uses pycryptodome for Windows 7 compatibility
# ============================================
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    USE_PYCRYPTODOME = True
except ImportError:
    USE_PYCRYPTODOME = False
    print("WARNING: pycryptodome not installed. Install with: pip install pycryptodome")

class EncryptionService:
    def __init__(self, key: str = None):
        key = key or ENCRYPTION_KEY
        key_bytes = key.encode()
        
        # Same logic as backend - ensure key is 32 bytes then base64 encode
        if len(key_bytes) < 32:
            padded_key = key_bytes.ljust(32, b'0')
        elif len(key_bytes) > 32:
            padded_key = key_bytes[:32]
        else:
            padded_key = key_bytes
        
        # This is the raw 32-byte key (first 16 = HMAC, last 16 = AES)
        self.signing_key = padded_key[:16]
        self.encryption_key = padded_key[16:32]
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt Fernet-encrypted data."""
        if not USE_PYCRYPTODOME:
            raise Exception("pycryptodome required for decryption. Run: pip install pycryptodome")
        
        # Decode the Fernet token
        data = base64.urlsafe_b64decode(encrypted_data.encode())
        
        # Parse Fernet token format:
        # version (1 byte) + timestamp (8 bytes) + IV (16 bytes) + ciphertext + HMAC (32 bytes)
        version = data[0]
        timestamp = data[1:9]
        iv = data[9:25]
        ciphertext_with_hmac = data[25:]
        
        # Last 32 bytes are HMAC, rest is ciphertext
        ciphertext = ciphertext_with_hmac[:-32]
        hmac_tag = ciphertext_with_hmac[-32:]
        
        # Decrypt with AES-128-CBC
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        
        return decrypted.decode()


# ============================================
# DATABASE CONNECTION (for inserting trades)
# ============================================
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# ============================================
# API FUNCTIONS (for getting accounts with decrypted passwords)
# ============================================
import requests

def get_accounts_to_sync() -> List[Dict]:
    """Get all active MT5 accounts that need syncing via API."""
    try:
        response = requests.get(
            f"{API_URL}/api/mt5/vps/accounts",
            headers={"X-VPS-Secret": ENCRYPTION_KEY},
            timeout=30
        )
        if response.status_code == 200:
            accounts = response.json()
            # Convert to expected format
            result = []
            for acc in accounts:
                result.append({
                    'id': acc['id'],
                    'user_id': acc['user_id'],
                    'mt5_login': acc['mt5_login'],
                    'mt5_password': acc['mt5_password'],  # Already decrypted!
                    'mt5_server': acc['mt5_server'],
                    'sync_interval_minutes': acc['sync_interval_minutes'],
                    'last_sync_at': acc.get('last_sync_at'),
                    'last_trade_time': acc.get('last_trade_time')
                })
            return result
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Failed to get accounts from API: {e}")
        return []


def update_sync_status(account_id: int, status: str, message: str, last_trade_time: datetime = None):
    """Update the sync status for an account via API."""
    try:
        payload = {
            "account_id": account_id,
            "status": status,
            "message": message
        }
        if last_trade_time:
            payload["last_trade_time"] = last_trade_time.isoformat()
        
        response = requests.post(
            f"{API_URL}/api/mt5/vps/status",
            headers={"X-VPS-Secret": ENCRYPTION_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        if response.status_code != 200:
            logger.error(f"Failed to update status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to update sync status via API: {e}")


def insert_trade(user_id: int, trade_data: Dict) -> bool:
    """Insert a trade into the database. Returns True if inserted, False if exists."""
    with Session() as session:
        # Check if trade already exists by MT5 ticket
        result = session.execute(text("""
            SELECT id FROM trades WHERE user_id = :user_id AND mt5_ticket = :ticket
        """), {'user_id': user_id, 'ticket': str(trade_data['ticket'])})
        
        if result.fetchone():
            return False  # Already exists
        
        # Insert new trade
        session.execute(text("""
            INSERT INTO trades (
                user_id, mt5_ticket, trade_source, symbol, trade_type, volume,
                open_price, close_price, stop_loss, take_profit,
                open_time, close_time, profit, commission, swap, net_profit,
                is_closed, created_at
            ) VALUES (
                :user_id, :mt5_ticket, 'mt5_auto', :symbol, :trade_type, :volume,
                :open_price, :close_price, :stop_loss, :take_profit,
                :open_time, :close_time, :profit, :commission, :swap, :net_profit,
                :is_closed, NOW()
            )
        """), {
            'user_id': user_id,
            'mt5_ticket': str(trade_data['ticket']),
            'symbol': trade_data['symbol'],
            'trade_type': trade_data['trade_type'],
            'volume': trade_data['volume'],
            'open_price': trade_data['open_price'],
            'close_price': trade_data.get('close_price'),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit': trade_data.get('take_profit'),
            'open_time': trade_data['open_time'],
            'close_time': trade_data.get('close_time'),
            'profit': trade_data.get('profit', 0),
            'commission': trade_data.get('commission', 0),
            'swap': trade_data.get('swap', 0),
            'net_profit': trade_data.get('net_profit', 0),
            'is_closed': trade_data.get('is_closed', False)
        })
        session.commit()
        return True


def sync_account(account: Dict) -> Tuple[bool, str, int]:
    """
    Sync trades for a single MT5 account.
    Returns: (success: bool, message: str, trades_synced: int)
    """
    try:
        # Password is already decrypted from API
        password = account['mt5_password']
        login = int(account['mt5_login'])
        server = account['mt5_server']
        
        logger.info(f"Connecting to MT5 for user {account['user_id']} (login: {login})")
        
        # Initialize MT5
        if not mt5.initialize():
            return False, f"MT5 initialization failed: {mt5.last_error()}", 0
        
        # Login to account
        if not mt5.login(login, password=password, server=server):
            error = mt5.last_error()
            mt5.shutdown()
            return False, f"Login failed: {error}", 0
        
        logger.info(f"Successfully logged in to {login}@{server}")
        
        # Get account info to verify connection
        account_info = mt5.account_info()
        if not account_info:
            mt5.shutdown()
            return False, "Could not get account info", 0
        
        # Get trade history
        # Start from last synced trade time or 1 year ago
        if account['last_trade_time']:
            from_date = account['last_trade_time']
        else:
            from_date = datetime.now(timezone.utc) - timedelta(days=365)
        
        to_date = datetime.now(timezone.utc)
        
        # Get closed deals (history)
        deals = mt5.history_deals_get(from_date, to_date)
        
        trades_synced = 0
        last_trade_time = account['last_trade_time']
        
        if deals:
            logger.info(f"Found {len(deals)} deals in history")
            
            # Group deals by position (entry and exit)
            positions = {}
            for deal in deals:
                # Skip balance operations, etc.
                if deal.type > 1:  # 0=BUY, 1=SELL, others are balance/credit/etc
                    continue
                
                pos_id = deal.position_id
                if pos_id not in positions:
                    positions[pos_id] = {'entry': None, 'exit': None}
                
                if deal.entry == 0:  # Entry deal
                    positions[pos_id]['entry'] = deal
                elif deal.entry == 1:  # Exit deal
                    positions[pos_id]['exit'] = deal
            
            # Process completed positions
            for pos_id, pos in positions.items():
                if pos['entry'] and pos['exit']:
                    entry = pos['entry']
                    exit = pos['exit']
                    
                    trade_data = {
                        'ticket': pos_id,
                        'symbol': entry.symbol,
                        'trade_type': 'buy' if entry.type == 0 else 'sell',
                        'volume': entry.volume,
                        'open_price': entry.price,
                        'close_price': exit.price,
                        'stop_loss': None,
                        'take_profit': None,
                        'open_time': datetime.fromtimestamp(entry.time, tz=timezone.utc),
                        'close_time': datetime.fromtimestamp(exit.time, tz=timezone.utc),
                        'profit': exit.profit,
                        'commission': entry.commission + exit.commission,
                        'swap': entry.swap + exit.swap if hasattr(entry, 'swap') else 0,
                        'net_profit': exit.profit + entry.commission + exit.commission,
                        'is_closed': True
                    }
                    
                    if insert_trade(account['user_id'], trade_data):
                        trades_synced += 1
                        trade_time = datetime.fromtimestamp(exit.time, tz=timezone.utc)
                        if not last_trade_time or trade_time > last_trade_time:
                            last_trade_time = trade_time
        
        # Also get open positions
        positions = mt5.positions_get()
        if positions:
            logger.info(f"Found {len(positions)} open positions")
            for pos in positions:
                trade_data = {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'trade_type': 'buy' if pos.type == 0 else 'sell',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'close_price': pos.price_current,
                    'stop_loss': pos.sl if pos.sl > 0 else None,
                    'take_profit': pos.tp if pos.tp > 0 else None,
                    'open_time': datetime.fromtimestamp(pos.time, tz=timezone.utc),
                    'close_time': None,
                    'profit': pos.profit,
                    'commission': pos.commission if hasattr(pos, 'commission') else 0,
                    'swap': pos.swap,
                    'net_profit': pos.profit,
                    'is_closed': False
                }
                
                if insert_trade(account['user_id'], trade_data):
                    trades_synced += 1
        
        # Shutdown MT5
        mt5.shutdown()
        
        message = f"Synced {trades_synced} new trades"
        logger.info(f"User {account['user_id']}: {message}")
        
        return True, message, trades_synced
        
    except Exception as e:
        logger.error(f"Error syncing account {account['user_id']}: {e}")
        logger.error(traceback.format_exc())
        try:
            mt5.shutdown()
        except:
            pass
        return False, f"Error: {str(e)}", 0


def run_sync_cycle():
    """Run one complete sync cycle for all accounts."""
    accounts = get_accounts_to_sync()
    
    if not accounts:
        logger.debug("No accounts need syncing")
        return
    
    logger.info(f"Found {len(accounts)} accounts to sync")
    
    for account in accounts:
        try:
            logger.info(f"Processing account ID {account['id']} (user {account['user_id']})")
            
            success, message, trades_synced = sync_account(account)
            
            update_sync_status(
                account['id'],
                'success' if success else 'error',
                message,
                datetime.now(timezone.utc) if trades_synced > 0 else None
            )
            
            # Small delay between accounts to be safe
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to sync account {account['id']}: {e}")
            update_sync_status(account['id'], 'error', str(e))


def main():
    """Main entry point - run the sync service forever."""
    logger.info("=" * 50)
    logger.info("MT5 Serial Sync Service Starting")
    logger.info("=" * 50)
    logger.info(f"Database: {DATABASE_URL[:50]}...")
    logger.info(f"Sync check interval: {SYNC_CHECK_INTERVAL} seconds")
    
    # Test MT5 initialization
    if not mt5.initialize():
        logger.error(f"MT5 initialization failed: {mt5.last_error()}")
        logger.error("Make sure MT5 terminal is installed")
        sys.exit(1)
    
    mt5.shutdown()
    logger.info("MT5 terminal found and working")
    
    # Main loop
    while True:
        try:
            run_sync_cycle()
        except Exception as e:
            logger.error(f"Error in sync cycle: {e}")
            logger.error(traceback.format_exc())
        
        logger.debug(f"Sleeping for {SYNC_CHECK_INTERVAL} seconds...")
        time.sleep(SYNC_CHECK_INTERVAL)


if __name__ == "__main__":
    main()
