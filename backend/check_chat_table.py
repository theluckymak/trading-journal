import os
os.environ['DATABASE_URL'] = "postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway"

from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    # Check if chat_messages table exists
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'chat_messages'"))
    tables = result.fetchall()
    print('chat_messages table exists:', len(tables) > 0)
    
    if len(tables) > 0:
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'chat_messages' ORDER BY ordinal_position"))
        print('Columns:')
        for row in result:
            print(f'  {row[0]}: {row[1]}')
    else:
        print("Table does not exist - need to run migrations!")
        # List all tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        print("Existing tables:")
        for row in result:
            print(f"  {row[0]}")
