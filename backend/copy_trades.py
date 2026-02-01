"""Copy trades from one user to another"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get user IDs
r1 = session.execute(text("SELECT id FROM users WHERE email = :e"), {"e": "tounsimoslim007@gmail.com"}).fetchone()
r2 = session.execute(text("SELECT id FROM users WHERE email = :e"), {"e": "yassinkaltoum83@gmail.com"}).fetchone()

source_id = r1[0]
target_id = r2[0]
print(f"Copying trades from user {source_id} to user {target_id}")

# Copy all trades from source to target
session.execute(text("""
    INSERT INTO trades (user_id, symbol, trade_type, volume, open_price, close_price, 
                       open_time, close_time, profit, commission, swap, net_profit, 
                       is_closed, trade_source, mt5_ticket, created_at, updated_at)
    SELECT :target_id, symbol, trade_type, volume, open_price, close_price,
           open_time, close_time, profit, commission, swap, net_profit,
           is_closed, trade_source, mt5_ticket, created_at, updated_at
    FROM trades WHERE user_id = :source_id
"""), {"source_id": source_id, "target_id": target_id})

session.commit()

# Count trades
count = session.execute(text("SELECT COUNT(*) FROM trades WHERE user_id = :id"), {"id": target_id}).fetchone()[0]
print(f"Done! User yassinkaltoum83@gmail.com now has {count} trades")
session.close()
