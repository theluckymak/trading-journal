"""
Generate sample trades with journals for testing
"""
import random
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/trading_journal')

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    trade_type = Column(String)
    volume = Column(Float)
    open_price = Column(Float)
    close_price = Column(Float)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    profit = Column(Float)
    commission = Column(Float)
    swap = Column(Float)
    is_closed = Column(Boolean)

class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    trade_id = Column(Integer)
    title = Column(String)
    content = Column(Text)
    tags = Column(ARRAY(String))
    mood = Column(String)

# Futures symbols with realistic price ranges
FUTURES = {
    'NQ': {'name': 'E-mini Nasdaq', 'price_range': (18000, 21000), 'tick': 0.25, 'multiplier': 20},
    'ES': {'name': 'E-mini S&P 500', 'price_range': (4500, 5200), 'tick': 0.25, 'multiplier': 50},
    'YM': {'name': 'E-mini Dow', 'price_range': (38000, 42000), 'tick': 1, 'multiplier': 5},
    'RTY': {'name': 'E-mini Russell', 'price_range': (1900, 2200), 'tick': 0.1, 'multiplier': 50},
    'CL': {'name': 'Crude Oil', 'price_range': (70, 85), 'tick': 0.01, 'multiplier': 1000},
    'GC': {'name': 'Gold', 'price_range': (2000, 2200), 'tick': 0.10, 'multiplier': 100},
    'SI': {'name': 'Silver', 'price_range': (23, 28), 'tick': 0.005, 'multiplier': 5000},
    'NG': {'name': 'Natural Gas', 'price_range': (2.5, 4.0), 'tick': 0.001, 'multiplier': 10000},
}

TRADE_SETUPS = [
    "Breakout above key resistance",
    "Pullback to support in uptrend",
    "Momentum continuation after news",
    "Gap fill opportunity",
    "Range breakout with volume",
    "Trend reversal at major level",
    "Failed breakout reversal",
    "Moving average crossover",
    "Support/resistance bounce",
    "Opening range breakout",
]

WIN_JOURNAL_TEMPLATES = [
    "Great trade! Stuck to my plan and let it run. Entry was perfect at {symbol} support.",
    "Patient entry paid off. Waited for confirmation and got {points} points profit.",
    "Solid risk management. Moved stop to breakeven early and captured the move.",
    "Market gave clear signals today. {symbol} trending strongly as expected.",
    "Best trade of the week! Recognized the pattern early and executed flawlessly.",
    "Followed my rules perfectly. Entry, stop loss, and exit all according to plan.",
    "Good discipline today. Didn't overtrade and took the high probability setup.",
    "Market conditions were favorable. {symbol} respected key levels beautifully.",
    "Nailed the entry timing. Waited for pullback and caught the continuation.",
    "Strong momentum in {symbol}. Rode the trend and secured profit.",
]

LOSS_JOURNAL_TEMPLATES = [
    "Got stopped out. Market reversed quickly. Need to widen stops in volatile conditions.",
    "Entered too early before confirmation. Should have waited for the pullback to complete.",
    "Market faked me out. {symbol} broke support but immediately reversed.",
    "Emotional trade. Got FOMO and entered without proper setup. Lesson learned.",
    "Stop was too tight for market conditions. Need to adjust for volatility.",
    "Missed the key reversal signal. Should have exited sooner when momentum shifted.",
    "Overtraded today. This was my 4th trade and I was tired. Should have stopped earlier.",
    "News moved market against me. Need to check economic calendar before trading.",
    "Got shaken out by volatility. Trade thesis was correct but stop placement was poor.",
    "Forced the trade. Setup wasn't fully formed but I took it anyway. Patience needed.",
]

def generate_trades(user_email: str, num_trades: int = 100, win_rate: float = 0.60):
    """Generate sample trades with journals"""
    
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find user
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User {user_email} not found!")
            return
        
        print(f"Generating {num_trades} trades for {user.email}...")
        
        # Determine win/loss distribution
        num_wins = int(num_trades * win_rate)
        num_losses = num_trades - num_wins
        outcomes = ['win'] * num_wins + ['loss'] * num_losses
        random.shuffle(outcomes)
        
        # Generate trades over last 90 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        created_trades = []
        
        for i in range(num_trades):
            # Random symbol
            symbol = random.choice(list(FUTURES.keys()))
            symbol_info = FUTURES[symbol]
            
            # Random date in range
            days_ago = random.randint(0, 90)
            trade_date = end_date - timedelta(days=days_ago)
            
            # Random trade type
            trade_type = random.choice(['buy', 'sell'])
            
            # Contracts (1-5 for most, occasionally more)
            volume = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[30, 25, 20, 10, 8, 4, 2, 1])[0]
            
            # Generate prices
            price_low, price_high = symbol_info['price_range']
            open_price = round(random.uniform(price_low, price_high), 2)
            
            # Determine if win or loss
            is_win = outcomes[i] == 'win'
            
            if is_win:
                # Winner: 5-50 points profit
                points = round(random.uniform(5, 50), 2)
            else:
                # Loser: -5 to -30 points
                points = round(random.uniform(-30, -5), 2)
            
            # Calculate close price based on trade direction
            if trade_type == 'buy':
                close_price = round(open_price + points, 2)
            else:
                close_price = round(open_price - points, 2)
            
            # Calculate P&L (points * multiplier * contracts)
            profit = round(points * symbol_info['multiplier'] * volume, 2)
            
            # Random commission and swap
            commission = round(random.uniform(2.0, 5.0) * volume, 2)
            swap = 0.0
            
            # Set trade times
            open_time = trade_date.replace(hour=random.randint(9, 15), minute=random.randint(0, 59))
            duration_minutes = random.randint(5, 180)  # 5 min to 3 hours
            close_time = open_time + timedelta(minutes=duration_minutes)
            
            # Create trade
            trade = Trade(
                user_id=user.id,
                symbol=symbol,
                trade_type=trade_type,
                volume=float(volume),
                open_price=float(open_price),
                close_price=float(close_price),
                open_time=open_time,
                close_time=close_time,
                profit=profit,
                commission=commission,
                swap=swap,
                is_closed=True,
            )
            
            session.add(trade)
            session.flush()  # Get trade.id
            
            # Create journal entry
            journal_templates = WIN_JOURNAL_TEMPLATES if is_win else LOSS_JOURNAL_TEMPLATES
            journal_content = random.choice(journal_templates).format(
                symbol=symbol,
                points=abs(points)
            )
            
            # Random mood based on outcome
            if is_win:
                mood = random.choices(['positive', 'neutral'], weights=[80, 20])[0]
            else:
                mood = random.choices(['negative', 'neutral'], weights=[70, 30])[0]
            
            # Random tags
            base_tags = [symbol, symbol_info['name'], random.choice(TRADE_SETUPS)]
            if is_win:
                base_tags.append(random.choice(['patience', 'discipline', 'good-entry', 'trend-following']))
            else:
                base_tags.append(random.choice(['lesson-learned', 'overtrading', 'fomo', 'stop-loss']))
            
            journal = JournalEntry(
                user_id=user.id,
                trade_id=trade.id,
                title=f"Trade: {symbol}",
                content=journal_content,
                tags=base_tags[:3],  # Keep 3 tags
                mood=mood,
            )
            
            session.add(journal)
            created_trades.append(trade)
            
            if (i + 1) % 10 == 0:
                print(f"Created {i + 1}/{num_trades} trades...")
        
        # Commit all
        session.commit()
        
        # Calculate stats
        total_profit = sum(t.profit for t in created_trades)
        winning_trades = [t for t in created_trades if t.profit > 0]
        losing_trades = [t for t in created_trades if t.profit < 0]
        actual_win_rate = len(winning_trades) / len(created_trades) * 100
        
        print(f"\n✅ Successfully created {num_trades} trades!")
        print(f"📊 Win Rate: {actual_win_rate:.1f}%")
        print(f"💰 Total P&L: ${total_profit:,.2f}")
        print(f"✅ Winning Trades: {len(winning_trades)}")
        print(f"❌ Losing Trades: {len(losing_trades)}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    generate_trades("yassinkaltoum83@gmail.com", num_trades=100, win_rate=0.60)
