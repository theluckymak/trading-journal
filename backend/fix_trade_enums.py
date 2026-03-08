"""Fix trade enum values to uppercase."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check current values
    print("Before fix:")
    r = conn.execute(text("SELECT trade_type, COUNT(*) FROM trades GROUP BY trade_type"))
    for row in r:
        print(f"  {row[0]}: {row[1]} trades")
    
    r = conn.execute(text("SELECT trade_source, COUNT(*) FROM trades GROUP BY trade_source"))
    print("\nTrade sources:")
    for row in r:
        print(f"  {row[0]}: {row[1]} trades")
    
    # Update lowercase to uppercase
    print("\nFixing lowercase values...")
    
    # Can't directly update enum values - need to use text casting
    # Update trade_type
    result = conn.execute(text("UPDATE trades SET trade_type = 'BUY' WHERE trade_type = 'buy'"))
    print(f"Updated {result.rowcount} 'buy' -> 'BUY'")
    
    result = conn.execute(text("UPDATE trades SET trade_type = 'SELL' WHERE trade_type = 'sell'"))
    print(f"Updated {result.rowcount} 'sell' -> 'SELL'")
    
    # Update trade_source
    result = conn.execute(text("UPDATE trades SET trade_source = 'MT5_AUTO' WHERE trade_source = 'mt5_auto'"))
    print(f"Updated {result.rowcount} 'mt5_auto' -> 'MT5_AUTO'")
    
    conn.commit()
    
    # Check after fix
    print("\nAfter fix:")
    r = conn.execute(text("SELECT trade_type, COUNT(*) FROM trades GROUP BY trade_type"))
    for row in r:
        print(f"  {row[0]}: {row[1]} trades")
    
    r = conn.execute(text("SELECT trade_source, COUNT(*) FROM trades GROUP BY trade_source"))
    print("\nTrade sources:")
    for row in r:
        print(f"  {row[0]}: {row[1]} trades")
