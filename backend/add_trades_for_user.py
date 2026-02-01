"""
Add realistic trades for a specific user via API
Run from Railway console or locally with DATABASE_URL set
"""
import random
from datetime import datetime, timedelta, timezone
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment or prompt
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("\n📊 Trade Generator for Trading Journal")
    print("=" * 50)
    print("\nPlease enter your Railway PostgreSQL DATABASE_URL")
    print("(Get this from Railway Dashboard > Postgres > Connect > Database URL)")
    print()
    DATABASE_URL = input("DATABASE_URL: ").strip()
    if not DATABASE_URL:
        print("❌ No DATABASE_URL provided!")
        sys.exit(1)

# Target user
TARGET_EMAIL = "tounsimoslim007@gmail.com"

# Futures symbols with realistic price ranges
FUTURES = {
    'NQ': {'name': 'E-mini Nasdaq', 'price_range': (18500, 20500), 'tick': 0.25, 'multiplier': 20},
    'ES': {'name': 'E-mini S&P 500', 'price_range': (4800, 5100), 'tick': 0.25, 'multiplier': 50},
    'MNQ': {'name': 'Micro Nasdaq', 'price_range': (18500, 20500), 'tick': 0.25, 'multiplier': 2},
    'MES': {'name': 'Micro S&P 500', 'price_range': (4800, 5100), 'tick': 0.25, 'multiplier': 5},
    'YM': {'name': 'E-mini Dow', 'price_range': (38000, 41000), 'tick': 1, 'multiplier': 5},
    'GC': {'name': 'Gold Futures', 'price_range': (2050, 2150), 'tick': 0.10, 'multiplier': 100},
    'CL': {'name': 'Crude Oil', 'price_range': (72, 82), 'tick': 0.01, 'multiplier': 1000},
}

# Trading setups
SETUPS = [
    "Opening Range Breakout",
    "Pullback to 9 EMA",
    "VWAP Bounce",
    "Previous Day High Break",
    "Previous Day Low Break",
    "Gap Fill",
    "Double Bottom Reversal",
    "Trend Continuation",
    "Failed Breakdown Long",
    "Failed Breakout Short",
    "Morning Momentum",
    "Afternoon Reversal",
    "Support Bounce",
    "Resistance Rejection",
    "Breakout Retest Entry",
]

def generate_trades():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find user
        result = session.execute(text("SELECT id FROM users WHERE email = :email"), {"email": TARGET_EMAIL})
        user_row = result.fetchone()
        
        if not user_row:
            print(f"User {TARGET_EMAIL} not found!")
            return
        
        user_id = user_row[0]
        print(f"Found user ID: {user_id}")
        
        # Generate 3000 trades over last 365 days with ~58% win rate
        num_trades = 3000
        win_rate = 0.58
        
        num_wins = int(num_trades * win_rate)
        outcomes = ['win'] * num_wins + ['loss'] * (num_trades - num_wins)
        random.shuffle(outcomes)
        
        now = datetime.now(timezone.utc)
        trades_added = 0
        total_pnl = 0
        
        for i in range(num_trades):
            # Random symbol - prefer NQ and ES
            symbol = random.choices(
                list(FUTURES.keys()), 
                weights=[35, 25, 15, 10, 5, 5, 5]
            )[0]
            info = FUTURES[symbol]
            
            # Random date in last 365 days (spread evenly)
            days_ago = int(random.triangular(0, 365, 60))
            trade_date = now - timedelta(days=days_ago)
            
            # Skip weekends
            while trade_date.weekday() >= 5:
                trade_date -= timedelta(days=1)
            
            # Trading hours (9:30 AM - 4:00 PM ET roughly)
            hour = random.choices([9, 10, 11, 12, 13, 14, 15], weights=[15, 25, 20, 10, 10, 10, 10])[0]
            minute = random.randint(0, 59)
            open_time = trade_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
            
            # Trade type (enum needs lowercase)
            trade_type = random.choice(['BUY', 'SELL'])
            
            # Volume (contracts) - mostly 1-3 for micros, 1-2 for minis
            if symbol in ['MNQ', 'MES']:
                volume = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            else:
                volume = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            
            # Open price
            low, high = info['price_range']
            open_price = round(random.uniform(low, high), 2)
            
            # Win or loss
            is_win = outcomes[i] == 'win'
            
            # Calculate points movement
            if is_win:
                # Winners: varied sizes, some big runners
                points = random.choices(
                    [random.uniform(3, 10), random.uniform(10, 25), random.uniform(25, 60), random.uniform(60, 120)],
                    weights=[40, 35, 20, 5]
                )[0]
            else:
                # Losers: mostly small (good risk management), some bigger
                points = random.choices(
                    [random.uniform(-5, -3), random.uniform(-12, -5), random.uniform(-25, -12), random.uniform(-40, -25)],
                    weights=[30, 45, 20, 5]
                )[0]
            
            points = round(points, 2)
            
            # Close price
            if trade_type == 'BUY':
                close_price = round(open_price + points, 2)
            else:
                close_price = round(open_price - points, 2)
            
            # P&L calculation
            profit = round(points * info['multiplier'] * volume, 2)
            total_pnl += profit
            
            # Commissions (realistic)
            commission = round(random.uniform(2.0, 4.5) * volume, 2)
            
            # Net P&L
            net_profit = round(profit - commission, 2)
            
            # Trade duration (5 min to 3 hours, some quick scalps, some longer)
            duration = random.choices(
                [random.randint(2, 10), random.randint(10, 30), random.randint(30, 90), random.randint(90, 180)],
                weights=[25, 35, 30, 10]
            )[0]
            close_time = open_time + timedelta(minutes=duration)
            
            # Setup
            setup = random.choice(SETUPS)
            
            # Notes
            if is_win:
                notes = random.choice([
                    f"Good entry on {setup}. Target hit.",
                    f"Clean {setup} setup. Followed plan.",
                    f"Patient entry, rode the move.",
                    f"Caught the momentum early.",
                    f"Nice {symbol} move, scaled out properly.",
                    "",
                ])
            else:
                notes = random.choice([
                    f"Stopped out. Market reversed.",
                    f"Entry was early, got shaken out.",
                    f"Setup failed. Cut loss quickly.",
                    f"Overtraded today.",
                    f"Choppy market, tough conditions.",
                    "",
                ])
            
            # Insert trade (without setup and notes - they don't exist in the table)
            session.execute(text("""
                INSERT INTO trades (user_id, symbol, trade_type, volume, open_price, close_price, 
                                   open_time, close_time, profit, commission, swap, net_profit, 
                                   is_closed, trade_source, created_at, updated_at)
                VALUES (:user_id, :symbol, :trade_type, :volume, :open_price, :close_price,
                       :open_time, :close_time, :profit, :commission, 0, :net_profit,
                       true, 'MANUAL', :created_at, :updated_at)
            """), {
                "user_id": user_id,
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
                "created_at": now,
                "updated_at": now,
            })
            
            trades_added += 1
            status = "WIN" if is_win else "LOSS"
            print(f"  [{trades_added}] {symbol} {trade_type.upper()} x{volume} | {status} | P&L: ${net_profit:+.2f}")
        
        session.commit()
        print(f"\n✅ Added {trades_added} trades for {TARGET_EMAIL}")
        print(f"📊 Total P&L: ${total_pnl:,.2f}")
        print(f"📈 Win Rate: {win_rate*100:.0f}%")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    generate_trades()
