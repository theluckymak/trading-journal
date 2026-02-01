"""
Add 1000 realistic trades over 1 year to multiple users
"""
import random
from datetime import datetime, timedelta, timezone
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway"

# Target users - add same trades to both
TARGET_EMAILS = [
    "tounsimoslim007@gmail.com",
    "yassinkaltoum83@gmail.com"
]

# Futures symbols with realistic price ranges and smaller multipliers for realistic P&L
FUTURES = {
    'NQ': {'price_range': (18500, 20500), 'multiplier': 20, 'weight': 30},
    'ES': {'price_range': (4800, 5100), 'multiplier': 50, 'weight': 25},
    'MNQ': {'price_range': (18500, 20500), 'multiplier': 2, 'weight': 20},
    'MES': {'price_range': (4800, 5100), 'multiplier': 5, 'weight': 15},
    'YM': {'price_range': (38000, 41000), 'multiplier': 5, 'weight': 5},
    'RTY': {'price_range': (2000, 2200), 'multiplier': 50, 'weight': 5},
}

def generate_trades_data(num_trades=1000, win_rate=0.55):
    """Generate trade data that can be reused for multiple users"""
    trades = []
    
    num_wins = int(num_trades * win_rate)
    outcomes = ['win'] * num_wins + ['loss'] * (num_trades - num_wins)
    random.shuffle(outcomes)
    
    now = datetime.now(timezone.utc)
    symbols = list(FUTURES.keys())
    weights = [FUTURES[s]['weight'] for s in symbols]
    
    for i in range(num_trades):
        # Random symbol
        symbol = random.choices(symbols, weights=weights)[0]
        info = FUTURES[symbol]
        
        # Random date in last 365 days
        days_ago = random.randint(0, 365)
        trade_date = now - timedelta(days=days_ago)
        
        # Skip weekends
        while trade_date.weekday() >= 5:
            trade_date -= timedelta(days=1)
        
        # Trading hours
        hour = random.choices([9, 10, 11, 12, 13, 14, 15], weights=[15, 25, 20, 10, 10, 10, 10])[0]
        minute = random.randint(0, 59)
        open_time = trade_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
        
        # Trade type
        trade_type = random.choice(['BUY', 'SELL'])
        
        # Volume - mostly small positions
        if symbol in ['MNQ', 'MES']:
            volume = random.choices([1, 2, 3, 4, 5], weights=[35, 30, 20, 10, 5])[0]
        else:
            volume = random.choices([1, 2, 3], weights=[65, 25, 10])[0]
        
        # Open price
        low, high = info['price_range']
        open_price = round(random.uniform(low, high), 2)
        
        # Win or loss
        is_win = outcomes[i] == 'win'
        
        # Calculate points - keep it realistic
        if is_win:
            if symbol in ['MNQ', 'MES']:
                points = random.uniform(5, 30)
            else:
                points = random.uniform(3, 20)
        else:
            if symbol in ['MNQ', 'MES']:
                points = -random.uniform(3, 20)
            else:
                points = -random.uniform(2, 15)
        
        points = round(points, 2)
        
        # Close price
        if trade_type == 'BUY':
            close_price = round(open_price + points, 2)
        else:
            close_price = round(open_price - points, 2)
        
        # P&L calculation
        profit = round(points * info['multiplier'] * volume, 2)
        
        # Commissions
        commission = round(random.uniform(2.0, 4.5) * volume, 2)
        
        # Net P&L
        net_profit = round(profit - commission, 2)
        
        # Trade duration
        duration = random.choices(
            [random.randint(2, 10), random.randint(10, 30), random.randint(30, 90), random.randint(90, 180)],
            weights=[25, 35, 30, 10]
        )[0]
        close_time = open_time + timedelta(minutes=duration)
        
        trades.append({
            "symbol": symbol,
            "trade_type": trade_type,
            "volume": float(volume),
            "open_price": float(open_price),
            "close_price": float(close_price),
            "open_time": open_time,
            "close_time": close_time,
            "profit": float(profit),
            "commission": float(commission),
            "net_profit": float(net_profit),
            "is_win": is_win,
        })
    
    return trades

def add_trades_to_user(session, user_id, trades, email):
    """Add trades to a specific user"""
    now = datetime.now(timezone.utc)
    count = 0
    total_pnl = 0
    
    for trade in trades:
        session.execute(text("""
            INSERT INTO trades (user_id, symbol, trade_type, volume, open_price, close_price, 
                               open_time, close_time, profit, commission, swap, net_profit, 
                               is_closed, trade_source, created_at, updated_at)
            VALUES (:user_id, :symbol, :trade_type, :volume, :open_price, :close_price,
                   :open_time, :close_time, :profit, :commission, 0, :net_profit,
                   true, 'MANUAL', :created_at, :updated_at)
        """), {
            "user_id": user_id,
            "symbol": trade["symbol"],
            "trade_type": trade["trade_type"],
            "volume": trade["volume"],
            "open_price": trade["open_price"],
            "close_price": trade["close_price"],
            "open_time": trade["open_time"],
            "close_time": trade["close_time"],
            "profit": trade["profit"],
            "commission": trade["commission"],
            "net_profit": trade["net_profit"],
            "created_at": now,
            "updated_at": now,
        })
        count += 1
        total_pnl += trade["net_profit"]
        
        if count % 100 == 0:
            print(f"  {email}: Added {count} trades...")
    
    return count, total_pnl

def main():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get user IDs
        users = {}
        for email in TARGET_EMAILS:
            result = session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
            user_row = result.fetchone()
            if user_row:
                users[email] = user_row[0]
                print(f"✓ Found user: {email} (ID: {user_row[0]})")
            else:
                print(f"✗ User not found: {email}")
        
        if not users:
            print("No users found!")
            return
        
        # Generate trades once
        print(f"\n📊 Generating 1000 trades over 1 year (55% win rate)...")
        trades = generate_trades_data(num_trades=1000, win_rate=0.55)
        
        wins = sum(1 for t in trades if t["is_win"])
        print(f"   Generated: {wins} wins, {1000 - wins} losses")
        
        # Add to each user
        for email, user_id in users.items():
            print(f"\n📈 Adding trades to {email}...")
            count, total_pnl = add_trades_to_user(session, user_id, trades, email)
            print(f"   ✅ Added {count} trades | Total P&L: ${total_pnl:,.2f}")
        
        session.commit()
        print(f"\n🎉 Done! Added 1000 identical trades to {len(users)} users.")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
