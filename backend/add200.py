"""Add 200 trades to both users"""
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

FUTURES = {
    'NQ': {'price_range': (18500, 20500), 'multiplier': 20},
    'ES': {'price_range': (4800, 5100), 'multiplier': 50},
    'MNQ': {'price_range': (18500, 20500), 'multiplier': 2},
    'MES': {'price_range': (4800, 5100), 'multiplier': 5},
}

now = datetime.now(timezone.utc)
user_ids = [16, 2]  # Both users

for user_id in user_ids:
    print(f"Adding 200 trades to user {user_id}...")
    for i in range(200):
        symbol = random.choice(['NQ', 'ES', 'MNQ', 'MES'])
        info = FUTURES[symbol]
        trade_type = random.choice(['BUY', 'SELL'])
        volume = random.randint(1, 3)
        
        days_ago = random.randint(0, 365)
        trade_date = now - timedelta(days=days_ago)
        while trade_date.weekday() >= 5:
            trade_date -= timedelta(days=1)
        
        open_time = trade_date.replace(hour=random.randint(9,15), minute=random.randint(0,59))
        close_time = open_time + timedelta(minutes=random.randint(5, 120))
        
        low, high = info['price_range']
        open_price = round(random.uniform(low, high), 2)
        
        is_win = random.random() < 0.55
        if is_win:
            points = random.uniform(5, 25)
        else:
            points = -random.uniform(3, 18)
        
        if trade_type == 'BUY':
            close_price = round(open_price + points, 2)
        else:
            close_price = round(open_price - points, 2)
        
        profit = round(points * info['multiplier'] * volume, 2)
        commission = round(random.uniform(2, 4) * volume, 2)
        net_profit = round(profit - commission, 2)
        
        session.execute(text("""
            INSERT INTO trades (user_id, symbol, trade_type, volume, open_price, close_price, 
                               open_time, close_time, profit, commission, swap, net_profit, 
                               is_closed, trade_source, created_at, updated_at)
            VALUES (:user_id, :symbol, :trade_type, :volume, :open_price, :close_price,
                   :open_time, :close_time, :profit, :commission, 0, :net_profit,
                   true, 'MANUAL', :created_at, :updated_at)
        """), {
            "user_id": user_id, "symbol": symbol, "trade_type": trade_type,
            "volume": float(volume), "open_price": open_price, "close_price": close_price,
            "open_time": open_time, "close_time": close_time, "profit": profit,
            "commission": commission, "net_profit": net_profit,
            "created_at": now, "updated_at": now,
        })
        
        if (i+1) % 50 == 0:
            print(f"  {i+1} trades added...")
    
    session.commit()
    print(f"✅ User {user_id}: 200 trades added")

# Final counts
for uid in [16, 2]:
    count = session.execute(text('SELECT COUNT(*) FROM trades WHERE user_id = :id'), {'id': uid}).fetchone()[0]
    print(f"User {uid} now has {count} trades")

session.close()
