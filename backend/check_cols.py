import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name='trades' ORDER BY ordinal_position"))
    for row in result:
        print(f"{row[0]}: {'NULL' if row[1]=='YES' else 'NOT NULL'} ({row[2]})")
