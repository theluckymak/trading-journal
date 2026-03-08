"""Delete MT5 auto-synced trades to allow proper re-sync."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Delete all MT5_AUTO trades for user 2 so they can re-sync properly
    result = conn.execute(text("""
        DELETE FROM trades 
        WHERE user_id = 2 AND trade_source = 'MT5_AUTO'
    """))
    conn.commit()
    print(f"Deleted {result.rowcount} MT5 auto-synced trades for user 2")
    print("They will re-sync on next sync cycle with correct data")
