"""
Diversify trades - remove some NQ and add other symbols
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.trade import Trade
from sqlalchemy import func

# Symbol configurations
SYMBOLS = {
    'ES': {'name': 'E-mini S&P 500', 'base_price': 4850.0, 'volatility': 50.0, 'point_value': 12.50, 'tick': 0.25},
    'YM': {'name': 'E-mini Dow', 'base_price': 38000.0, 'volatility': 200.0, 'point_value': 5.0, 'tick': 1.0},
    'GC': {'name': 'Gold', 'base_price': 2050.0, 'volatility': 30.0, 'point_value': 10.0, 'tick': 0.10},
    'CL': {'name': 'Crude Oil', 'base_price': 72.0, 'volatility': 2.5, 'point_value': 10.0, 'tick': 0.01},
    'EUR/USD': {'name': 'Euro', 'base_price': 1.0920, 'volatility': 0.008, 'point_value': 12.50, 'tick': 0.0001},
}

def generate_price(symbol, base_price, days_offset):
    """Generate realistic price based on symbol"""
    config = SYMBOLS[symbol]
    drift = days_offset * (config['volatility'] / 100)
    volatility = random.gauss(0, config['volatility'])
    return base_price + drift + volatility

def generate_trade_outcome(is_winner, entry_price, trade_type, volume, symbol):
    """Generate realistic trade outcome for any symbol"""
    config = SYMBOLS[symbol]
    point_value = config['point_value']
    
    if is_winner:
        # Winners: variable based on symbol
        if symbol == 'ES':
            points = random.uniform(8, 40)
        elif symbol == 'YM':
            points = random.uniform(30, 150)
        elif symbol == 'GC':
            points = random.uniform(5, 25)
        elif symbol == 'CL':
            points = random.uniform(0.3, 1.5)
        elif symbol == 'EUR/USD':
            points = random.uniform(15, 60)  # pips
        multiplier = 1
    else:
        # Losers
        if symbol == 'ES':
            points = random.uniform(5, 28)
        elif symbol == 'YM':
            points = random.uniform(20, 100)
        elif symbol == 'GC':
            points = random.uniform(3, 18)
        elif symbol == 'CL':
            points = random.uniform(0.2, 1.0)
        elif symbol == 'EUR/USD':
            points = random.uniform(10, 45)  # pips
        multiplier = -1
    
    # Calculate price movement
    if symbol == 'EUR/USD':
        price_movement = points * 0.0001 * multiplier  # pips
    else:
        price_movement = points * config['tick'] * multiplier
    
    # Adjust for trade type
    if trade_type == 'buy':
        close_price = entry_price + price_movement
    else:
        close_price = entry_price - price_movement
    
    gross_profit = points * point_value * volume * multiplier
    commission = -2.50 * 2 * volume  # $2.50 per side
    swap = random.uniform(-0.5, -5.0) * volume
    net_profit = gross_profit + commission + swap
    
    return close_price, gross_profit, commission, swap, net_profit

def diversify_trades():
    """Remove some NQ trades and add other symbols"""
    db = next(get_db())
    
    # Get current NQ trades count
    nq_count = db.query(func.count(Trade.id)).filter(Trade.symbol == 'NQ').scalar()
    print(f"Current NQ trades: {nq_count}")
    
    # Keep 150 NQ trades, delete the rest
    if nq_count > 150:
        trades_to_delete = nq_count - 150
        print(f"Deleting {trades_to_delete} NQ trades...")
        
        # Get random NQ trade IDs to delete
        nq_trades = db.query(Trade.id).filter(Trade.symbol == 'NQ').all()
        ids_to_delete = random.sample([t.id for t in nq_trades], trades_to_delete)
        
        db.query(Trade).filter(Trade.id.in_(ids_to_delete)).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {trades_to_delete} NQ trades")
    
    # Generate trades for other symbols
    # Distribution: ES (30), YM (20), GC (20), CL (10), EUR/USD (11) = 91 trades
    symbol_distribution = {
        'ES': 30,
        'YM': 20,
        'GC': 20,
        'CL': 10,
        'EUR/USD': 11
    }
    
    start_date = datetime.now() - timedelta(days=120)
    win_rate = 0.63
    
    all_new_trades = []
    
    for symbol, count in symbol_distribution.items():
        print(f"Generating {count} {symbol} trades...")
        
        num_winners = int(count * win_rate)
        num_losers = count - num_winners
        outcomes = ([True] * num_winners) + ([False] * num_losers)
        random.shuffle(outcomes)
        
        config = SYMBOLS[symbol]
        
        for i in range(count):
            days_offset = random.uniform(0, 120)
            open_time = start_date + timedelta(days=days_offset)
            
            # Trade duration
            if random.random() < 0.85:
                duration_minutes = random.uniform(5, 300)
            else:
                duration_minutes = random.uniform(480, 2880)
            
            close_time = open_time + timedelta(minutes=duration_minutes)
            trade_type = random.choice(['buy', 'sell'])
            volume = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            
            entry_price = generate_price(symbol, config['base_price'], days_offset)
            is_winner = outcomes[i]
            
            close_price, gross_profit, commission, swap, net_profit = generate_trade_outcome(
                is_winner, entry_price, trade_type, volume, symbol
            )
            
            # Format prices appropriately
            if symbol == 'EUR/USD':
                entry_price = round(entry_price, 4)
                close_price = round(close_price, 4)
            elif symbol == 'CL':
                entry_price = round(entry_price, 2)
                close_price = round(close_price, 2)
            else:
                entry_price = round(entry_price, 2)
                close_price = round(close_price, 2)
            
            trade = Trade(
                user_id=4,
                symbol=symbol,
                trade_type=trade_type,
                volume=volume,
                open_price=entry_price,
                close_price=close_price,
                open_time=open_time,
                close_time=close_time,
                profit=round(gross_profit, 2),
                commission=round(commission, 2),
                swap=round(swap, 2),
                net_profit=round(net_profit, 2),
                is_closed=True,
                trade_source='manual'
            )
            
            all_new_trades.append(trade)
    
    print(f"Inserting {len(all_new_trades)} new trades...")
    db.bulk_save_objects(all_new_trades)
    db.commit()
    
    # Show summary by symbol
    print("\n" + "="*60)
    print("PORTFOLIO SUMMARY")
    print("="*60)
    
    for symbol in ['NQ', 'ES', 'YM', 'GC', 'CL', 'EUR/USD']:
        trades = db.query(Trade).filter(Trade.symbol == symbol, Trade.is_closed == True).all()
        if trades:
            count = len(trades)
            winners = len([t for t in trades if t.net_profit > 0])
            total_pl = sum(t.net_profit for t in trades)
            
            print(f"{symbol:8} | Trades: {count:3} | Win Rate: {winners/count*100:5.1f}% | P/L: ${total_pl:>10,.2f}")
    
    # Overall stats
    all_trades = db.query(Trade).filter(Trade.is_closed == True).all()
    total_count = len(all_trades)
    total_winners = len([t for t in all_trades if t.net_profit > 0])
    total_pl = sum(t.net_profit for t in all_trades)
    
    print("-"*60)
    print(f"{'TOTAL':8} | Trades: {total_count:3} | Win Rate: {total_winners/total_count*100:5.1f}% | P/L: ${total_pl:>10,.2f}")
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    try:
        diversify_trades()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
