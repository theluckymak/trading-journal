"""Debug user and trades."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check user 2 details
    print("User 2 details:")
    r = conn.execute(text("SELECT id, email, is_active, is_verified FROM users WHERE id = 2"))
    for row in r:
        print(f"  ID: {row[0]}, Email: {row[1]}, Active: {row[2]}, Verified: {row[3]}")
    
    # Check trades for user 2
    print("\nTrades for user 2 (first 5):")
    r = conn.execute(text("SELECT id, symbol, trade_type, profit, open_time, is_closed FROM trades WHERE user_id = 2 ORDER BY id DESC LIMIT 5"))
    for row in r:
        print(f"  ID: {row[0]}, Symbol: {row[1]}, Type: {row[2]}, Profit: {row[3]}, Open: {row[4]}, Closed: {row[5]}")
    
    # Count total trades for user 2
    r = conn.execute(text("SELECT COUNT(*) FROM trades WHERE user_id = 2"))
    count = r.fetchone()[0]
    print(f"\nTotal trades for user 2: {count}")
