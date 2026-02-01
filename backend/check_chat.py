from sqlalchemy import create_engine, text
DATABASE_URL = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_messages'"))
    columns = [row[0] for row in result]
    print('chat_messages columns:', columns)
