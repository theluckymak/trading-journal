"""Check trades in the database."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check recent trades
    r = conn.execute(text('SELECT id, user_id, symbol, trade_type, trade_source, profit, is_closed FROM trades ORDER BY id DESC LIMIT 10'))
    print("Recent trades:")
    for row in r:
        print(row)
    
    # Check total trades per user
    print("\nTrades per user:")
    r = conn.execute(text('SELECT user_id, COUNT(*) as count FROM trades GROUP BY user_id'))
    for row in r:
        print(f"User {row[0]}: {row[1]} trades")
    
    # Check users
    print("\nUsers:")
    r = conn.execute(text('SELECT id, email FROM users LIMIT 10'))
    for row in r:
        print(f"User {row[0]}: {row[1]}")
