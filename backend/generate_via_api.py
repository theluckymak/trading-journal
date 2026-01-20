"""
Generate 100 sample trades using the API endpoint
"""
import requests
import random
from datetime import datetime, timedelta

# API configuration
BASE_URL = "https://dependable-solace-production-75f7.up.railway.app"

# Login credentials (you'll need to provide a valid token)
# First, we need to login and get a token
def login(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

# Futures data
FUTURES = {
    'NQ': {'name': 'E-mini Nasdaq', 'price_range': (18000, 21000), 'tick': 0.25, 'multiplier': 20},
    'ES': {'name': 'E-mini S&P 500', 'price_range': (4500, 5200), 'tick': 0.25, 'multiplier': 50},
    'YM': {'name': 'E-mini Dow', 'price_range': (38000, 42000), 'tick': 1.0, 'multiplier': 5},
    'RTY': {'name': 'E-mini Russell 2000', 'price_range': (1900, 2200), 'tick': 0.1, 'multiplier': 50},
    'CL': {'name': 'Crude Oil', 'price_range': (70, 85), 'tick': 0.01, 'multiplier': 1000},
    'GC': {'name': 'Gold', 'price_range': (1900, 2100), 'tick': 0.1, 'multiplier': 100},
    'SI': {'name': 'Silver', 'price_range': (22, 26), 'tick': 0.005, 'multiplier': 5000},
    'NG': {'name': 'Natural Gas', 'price_range': (2.5, 4.0), 'tick': 0.001, 'multiplier': 10000},
}

SETUPS = ['Breakout', 'Pullback', 'Trend', 'Reversal', 'Range', 'Momentum', 'News']
WIN_MOODS = ['confident', 'excited', 'neutral', 'focused']
LOSS_MOODS = ['disappointed', 'neutral', 'frustrated', 'reflective']

WIN_JOURNAL_TEMPLATES = [
    "Great execution today. Followed my plan perfectly and the setup worked exactly as expected. {symbol} showed strong momentum and I managed to capture most of the move.",
    "Excellent trade on {symbol}. Entry was precise at {entry_price} and I let my winner run to {exit_price}. Risk management was on point with proper position sizing of {contracts} contracts.",
    "Solid win. The {setup} setup on {symbol} developed beautifully. Got in early at {entry_price} and took profits at {exit_price} for a clean ${profit} gain.",
    "Very satisfied with this trade. {symbol} respected key levels and my analysis was correct. Managed the trade well from entry to exit, banking ${profit}.",
    "Clean execution on {symbol}. The market gave me a perfect {setup} setup and I capitalized on it. Entry at {entry_price}, exit at {exit_price} for +${profit}.",
    "Strong trade today. {symbol} showed clear direction and I positioned {contracts} contracts perfectly. The move from {entry_price} to {exit_price} netted ${profit}.",
    "Textbook {setup} setup on {symbol}. Everything aligned - price action, volume, and momentum. Executed flawlessly for ${profit} profit.",
    "Disciplined trading paid off. Waited for the right setup on {symbol} and got rewarded with a nice ${profit} gain. Entry and exit were both optimal.",
    "Great read on {symbol}. The {setup} pattern played out perfectly. Position of {contracts} contracts from {entry_price} to {exit_price} = ${profit}.",
    "Profitable session. {symbol} gave a clean signal and I took it without hesitation. Risk was well-defined and the reward was excellent at ${profit}."
]

LOSS_JOURNAL_TEMPLATES = [
    "Tough loss on {symbol}. The {setup} setup looked good but market conditions changed. Stopped out at {exit_price} for -${loss}. Need to work on reading momentum shifts better.",
    "Took a loss today on {symbol}. Entry at {entry_price} was premature - should have waited for confirmation. Lost ${loss} but kept it within risk parameters.",
    "Disappointing trade. {symbol} reversed on me after entry. Position of {contracts} contracts hit stop at {exit_price} for -${loss}. Market was choppier than expected.",
    "Learning experience on {symbol}. The {setup} setup failed as price action didn't follow through. Managed risk properly and took the -${loss} loss without hesitation.",
    "Not my best read. {symbol} looked strong but momentum faded quickly. Exit at {exit_price} resulted in ${loss} loss. Will review the setup criteria for next time.",
    "Protected my capital today. {symbol} didn't work out as the {setup} setup broke down. Stopped out with {contracts} contracts for -${loss}. Stop loss did its job.",
    "Quick loss on {symbol}. Market gave a false signal and I got caught. From {entry_price} to {exit_price} = -${loss}. Need to tighten entry criteria.",
    "Respected my stop on {symbol}. The trade went against me immediately and I cut it at {exit_price}. -${loss} loss but that's trading. Better setups tomorrow.",
    "Tough market conditions today. {symbol} showed a {setup} but volatility was too high. Took -${loss} loss and stepped aside. Proper risk management in action.",
    "Losing trade but controlled damage. {symbol} didn't provide the follow-through I expected. Exit at {exit_price} kept loss to ${loss}. Review and move on."
]

def generate_trade_data(symbol_key, is_winner, base_date):
    """Generate realistic trade data"""
    symbol_info = FUTURES[symbol_key]
    price_low, price_high = symbol_info['price_range']
    tick = symbol_info['tick']
    multiplier = symbol_info['multiplier']
    
    # Generate entry price
    entry_price = round(random.uniform(price_low, price_high) / tick) * tick
    
    # Generate realistic price movement
    if is_winner:
        # Winners: 5-40 ticks profit
        ticks_moved = random.randint(5, 40)
        exit_price = entry_price + (ticks_moved * tick) if random.random() > 0.5 else entry_price - (ticks_moved * tick)
    else:
        # Losers: 3-15 ticks loss
        ticks_moved = random.randint(3, 15)
        exit_price = entry_price - (ticks_moved * tick) if random.random() > 0.5 else entry_price + (ticks_moved * tick)
    
    # Round to proper tick size
    exit_price = round(exit_price / tick) * tick
    
    # Determine trade type based on price movement
    trade_type = "buy" if exit_price > entry_price else "sell"
    
    # Calculate contracts (weighted toward smaller sizes)
    contracts = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[35, 25, 15, 10, 7, 4, 2, 2])[0]
    
    # Calculate P&L
    points_moved = abs(exit_price - entry_price)
    gross_pnl = points_moved * multiplier * contracts
    commission = 4.00 * contracts  # $4 per contract round trip
    net_pnl = gross_pnl - commission if is_winner else -(gross_pnl + commission)
    
    # Generate times (random time during trading session)
    hours_offset = random.uniform(0, 23)
    minutes_offset = random.uniform(5, 180)  # 5 minutes to 3 hours
    
    open_time = base_date + timedelta(hours=hours_offset)
    close_time = open_time + timedelta(minutes=minutes_offset)
    
    # Generate stop loss and take profit
    stop_distance = random.randint(10, 25) * tick
    tp_distance = random.randint(20, 50) * tick
    
    if trade_type == "buy":
        stop_loss = round((entry_price - stop_distance) / tick) * tick
        take_profit = round((entry_price + tp_distance) / tick) * tick
    else:
        stop_loss = round((entry_price + stop_distance) / tick) * tick
        take_profit = round((entry_price - tp_distance) / tick) * tick
    
    setup = random.choice(SETUPS)
    
    return {
        'symbol': symbol_key,
        'trade_type': trade_type,
        'volume': float(contracts),
        'open_price': float(entry_price),
        'close_price': float(exit_price),
        'open_time': open_time.isoformat(),
        'close_time': close_time.isoformat(),
        'stop_loss': float(stop_loss),
        'take_profit': float(take_profit),
        'profit': float(round(net_pnl, 2)),
        'commission': float(commission),
        'swap': 0.0,
        'is_closed': True,
    }, {
        'setup': setup,
        'contracts': contracts,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'profit_abs': abs(net_pnl)
    }

def generate_journal_content(symbol, is_winner, template_vars):
    """Generate journal content"""
    if is_winner:
        template = random.choice(WIN_JOURNAL_TEMPLATES)
        mood = random.choice(WIN_MOODS)
        tags = f"{symbol},{template_vars['setup']},Winner,Discipline"
    else:
        template = random.choice(LOSS_JOURNAL_TEMPLATES)
        mood = random.choice(LOSS_MOODS)
        tags = f"{symbol},{template_vars['setup']},Loss,Learning"
    
    content = template.format(
        symbol=symbol,
        setup=template_vars['setup'],
        contracts=template_vars['contracts'],
        entry_price=template_vars['entry_price'],
        exit_price=template_vars['exit_price'],
        profit=f"{template_vars['profit_abs']:.2f}",
        loss=f"{template_vars['profit_abs']:.2f}"
    )
    
    return {
        'content': content,
        'tags': tags,
        'mood': mood
    }

def create_trade_with_journal(token, trade_data, journal_data):
    """Create trade and journal via API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create trade
    response = requests.post(
        f"{BASE_URL}/trades",
        json=trade_data,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"Failed to create trade: {response.status_code} - {response.text}")
        return False
    
    trade = response.json()
    trade_id = trade['id']
    
    # Create journal entry
    journal_payload = {
        'trade_id': trade_id,
        **journal_data
    }
    
    response = requests.post(
        f"{BASE_URL}/journal/entries",
        json=journal_payload,
        headers=headers
    )
    
    if response.status_code != 201:
        print(f"Failed to create journal for trade {trade_id}: {response.status_code} - {response.text}")
        return False
    
    return True

def main():
    print("Sample Trade Generator via API")
    print("=" * 50)
    
    # Hardcoded credentials for yassinkaltoum83@gmail.com
    email = "yassinkaltoum83@gmail.com"
    password = "123456Aa"
    
    # Login
    print(f"\nLogging in as {email}...")
    try:
        token = login(email, password)
        print("✓ Login successful!")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return
    
    # Generate trades
    print("\nGenerating 100 trades...")
    
    # 60% winners, 40% losers
    outcomes = [True] * 60 + [False] * 40
    random.shuffle(outcomes)
    
    # Generate over past 90 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    successful = 0
    failed = 0
    
    for i, is_winner in enumerate(outcomes):
        # Random date within range
        days_offset = random.uniform(0, 90)
        trade_date = start_date + timedelta(days=days_offset)
        
        # Random symbol
        symbol = random.choice(list(FUTURES.keys()))
        
        # Generate trade and journal data
        trade_data, template_vars = generate_trade_data(symbol, is_winner, trade_date)
        journal_data = generate_journal_content(symbol, is_winner, template_vars)
        
        # Create via API
        if create_trade_with_journal(token, trade_data, journal_data):
            successful += 1
            print(f"✓ Trade {i+1}/100 created ({symbol}, {'WIN' if is_winner else 'LOSS'})")
        else:
            failed += 1
            print(f"✗ Trade {i+1}/100 failed")
    
    print("\n" + "=" * 50)
    print(f"Generation complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {successful + failed}")
    
    if successful > 0:
        print("\n✓ Trades have been generated! Login to see them in your dashboard.")

if __name__ == "__main__":
    main()
