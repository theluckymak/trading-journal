"""
Generate 231 realistic NQ trades with 63% win rate
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, engine
from app.models.trade import Trade
from sqlalchemy.orm import Session

# NQ typical price range (adjusted for 2026)
NQ_BASE_PRICE = 18500.0
NQ_DAILY_VOLATILITY = 200.0

def generate_nq_price(base_price, days_offset):
    """Generate realistic NQ price based on time"""
    drift = days_offset * 2.5  # Slight upward drift
    volatility = random.gauss(0, NQ_DAILY_VOLATILITY)
    return base_price + drift + volatility

def generate_trade_outcome(is_winner, entry_price, trade_type, volume):
    """Generate realistic trade outcome"""
    # NQ moves in 0.25 increments, worth $5 each
    point_value = 5.0
    
    if is_winner:
        # Winners: 10-50 points profit (average ~25 points)
        points = random.uniform(10, 50)
        multiplier = 1  # Profit
    else:
        # Losers: -8 to -35 points loss (average ~-18 points, 1:1.4 R:R)
        points = random.uniform(8, 35)
        multiplier = -1  # Loss
    
    # Calculate price movement
    price_movement = points * 0.25 * multiplier
    
    # Adjust for trade type
    if trade_type == 'buy':
        close_price = entry_price + price_movement
    else:  # sell
        close_price = entry_price - price_movement
    
    gross_profit = points * point_value * volume * multiplier
    
    # Commission: ~$2.50 per side per contract
    commission = -2.50 * 2 * volume
    
    # Swap (overnight fee): small for day trades, larger for multi-day
    swap = random.uniform(-0.5, -5.0) * volume
    
    net_profit = gross_profit + commission + swap
    
    return close_price, gross_profit, commission, swap, net_profit

def generate_trades(user_id=4, total_trades=231, win_rate=0.63):
    """Generate realistic NQ trades"""
    db = next(get_db())
    
    # Calculate number of winners and losers
    num_winners = int(total_trades * win_rate)
    num_losers = total_trades - num_winners
    
    print(f"Generating {total_trades} NQ trades ({num_winners} winners, {num_losers} losers)")
    
    # Create list of outcomes (True = winner, False = loser)
    outcomes = ([True] * num_winners) + ([False] * num_losers)
    random.shuffle(outcomes)
    
    # Generate trades over the past 120 days
    start_date = datetime.now() - timedelta(days=120)
    
    trades = []
    for i in range(total_trades):
        # Random date within the period
        days_offset = random.uniform(0, 120)
        open_time = start_date + timedelta(days=days_offset)
        
        # Trade duration: mostly day trades (minutes to hours)
        if random.random() < 0.85:  # 85% day trades
            duration_minutes = random.uniform(5, 300)  # 5 min to 5 hours
        else:  # 15% swing trades
            duration_minutes = random.uniform(480, 2880)  # 8 hours to 2 days
        
        close_time = open_time + timedelta(minutes=duration_minutes)
        
        # Random trade type
        trade_type = random.choice(['buy', 'sell'])
        
        # Volume: 1-3 contracts (mostly 1)
        volume = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        
        # Entry price
        entry_price = round(generate_nq_price(NQ_BASE_PRICE, days_offset), 2)
        
        # Generate outcome
        is_winner = outcomes[i]
        close_price, gross_profit, commission, swap, net_profit = generate_trade_outcome(
            is_winner, entry_price, trade_type, volume
        )
        
        # Create trade
        trade = Trade(
            user_id=user_id,
            symbol="NQ",
            trade_type=trade_type,
            volume=volume,
            open_price=round(entry_price, 2),
            close_price=round(close_price, 2),
            open_time=open_time,
            close_time=close_time,
            profit=round(gross_profit, 2),
            commission=round(commission, 2),
            swap=round(swap, 2),
            net_profit=round(net_profit, 2),
            is_closed=True,
            trade_source='manual'
        )
        
        trades.append(trade)
        
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1}/{total_trades} trades...")
    
    # Bulk insert
    print("Inserting trades into database...")
    db.bulk_save_objects(trades)
    db.commit()
    
    # Calculate statistics
    total_profit = sum(t.net_profit for t in trades)
    winners = [t for t in trades if t.net_profit > 0]
    losers = [t for t in trades if t.net_profit <= 0]
    
    avg_win = sum(t.net_profit for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t.net_profit for t in losers) / len(losers) if losers else 0
    
    print("\n" + "="*60)
    print(f"Successfully generated {total_trades} NQ trades!")
    print("="*60)
    print(f"Total Profit: ${total_profit:,.2f}")
    print(f"Winners: {len(winners)} ({len(winners)/total_trades*100:.1f}%)")
    print(f"Losers: {len(losers)} ({len(losers)/total_trades*100:.1f}%)")
    print(f"Average Win: ${avg_win:,.2f}")
    print(f"Average Loss: ${avg_loss:,.2f}")
    print(f"Profit Factor: {abs(sum(t.net_profit for t in winners) / sum(t.net_profit for t in losers)):.2f}" if losers else "N/A")
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    try:
        generate_trades()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
