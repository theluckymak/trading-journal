import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

engine = create_engine(os.environ['DATABASE_URL'])

# Find user
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, full_name FROM users WHERE email = 'louayykaltoum@gmail.com'"))
    user = result.fetchone()
    if user:
        print(f'User found: ID={user[0]}, Email={user[1]}, Name={user[2]}')
        user_id = user[0]
    else:
        print('User not found')
        exit()

# Generate 200 trades
symbols = ['NQ', 'ES', 'MNQ', 'MES', 'YM', 'RTY', 'CL', 'GC', 'EURUSD', 'GBPUSD']
trade_types = ['BUY', 'SELL']

trades_added = 0
with engine.connect() as conn:
    for i in range(200):
        symbol = random.choice(symbols)
        trade_type = random.choice(trade_types)
        
        # Random date in last year
        days_ago = random.randint(1, 365)
        open_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        close_time = open_time + timedelta(minutes=random.randint(5, 480))
        
        # Price based on symbol
        if symbol in ['NQ', 'MNQ']:
            base_price = random.uniform(17000, 21000)
        elif symbol in ['ES', 'MES']:
            base_price = random.uniform(4800, 5500)
        elif symbol == 'YM':
            base_price = random.uniform(38000, 42000)
        elif symbol == 'RTY':
            base_price = random.uniform(2000, 2300)
        elif symbol == 'CL':
            base_price = random.uniform(70, 90)
        elif symbol == 'GC':
            base_price = random.uniform(1900, 2100)
        else:
            base_price = random.uniform(1.0, 1.5)
        
        open_price = round(base_price, 2)
        
        # Profit/loss
        if random.random() < 0.55:  # 55% win rate
            if trade_type == 'BUY':
                close_price = round(open_price * random.uniform(1.001, 1.02), 2)
            else:
                close_price = round(open_price * random.uniform(0.98, 0.999), 2)
            profit = abs(close_price - open_price) * random.randint(1, 5) * 100
        else:
            if trade_type == 'BUY':
                close_price = round(open_price * random.uniform(0.98, 0.999), 2)
            else:
                close_price = round(open_price * random.uniform(1.001, 1.02), 2)
            profit = -abs(close_price - open_price) * random.randint(1, 5) * 100
        
        profit = round(profit, 2)
        volume = random.randint(1, 5)
        commission = round(random.uniform(2, 10), 2)
        net_profit = round(profit - commission, 2)
        
        conn.execute(text("""
            INSERT INTO trades (user_id, symbol, trade_type, volume, open_price, close_price, 
                               profit, commission, swap, net_profit, open_time, close_time, is_closed, created_at, trade_source)
            VALUES (:user_id, :symbol, :trade_type, :volume, :open_price, :close_price,
                   :profit, :commission, 0, :net_profit, :open_time, :close_time, true, :created_at, 'MANUAL')
        """), {
            'user_id': user_id,
            'symbol': symbol,
            'trade_type': trade_type,
            'volume': volume,
            'open_price': open_price,
            'close_price': close_price,
            'profit': profit,
            'commission': commission,
            'net_profit': net_profit,
            'open_time': open_time,
            'close_time': close_time,
            'created_at': open_time
        })
        trades_added += 1
    
    conn.commit()

print(f'Added {trades_added} trades to user {user_id}')

# Verify count
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM trades WHERE user_id = :uid"), {'uid': user_id})
    count = result.scalar()
    print(f'Total trades for user {user_id}: {count}')
