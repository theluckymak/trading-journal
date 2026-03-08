"""Fix enum values in Railway database."""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql+pg8000://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check existing enum values
    r = conn.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tradetype')"))
    print("tradetype values:", [row[0] for row in r])
    
    r = conn.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tradesource')"))
    print("tradesource values:", [row[0] for row in r])
