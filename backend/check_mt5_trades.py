"""Check MT5 synced trades."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("MT5 Auto-synced trades for user 2:")
    r = conn.execute(text("""
        SELECT id, mt5_ticket, symbol, trade_type, volume, profit, close_time, is_closed 
        FROM trades 
        WHERE user_id = 2 AND trade_source = 'MT5_AUTO' 
        ORDER BY id DESC
    """))
    for row in r:
        print(f"ID:{row[0]} Ticket:{row[1]} {row[2]} {row[3]} vol={row[4]} profit={row[5]} closed={row[7]} close_time={row[6]}")
