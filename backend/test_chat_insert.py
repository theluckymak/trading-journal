import os
os.environ['DATABASE_URL'] = "postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

# Test creating a message directly
with engine.connect() as conn:
    # Get user 2 info
    result = conn.execute(text("SELECT id, email, role, full_name FROM users WHERE id = 2"))
    user = result.fetchone()
    print(f"User 2: {user}")
    
    # Try to insert a test message
    try:
        conn.execute(text("""
            INSERT INTO chat_messages (user_id, conversation_user_id, message, is_admin, created_at)
            VALUES (2, 2, 'Test message from script', false, NOW())
        """))
        conn.commit()
        print("Message inserted successfully!")
        
        # Read it back with user info
        result = conn.execute(text("""
            SELECT cm.id, cm.message, u.email, u.full_name
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.user_id = 2
            ORDER BY cm.created_at DESC
            LIMIT 1
        """))
        msg = result.fetchone()
        print(f"Message: {msg}")
        
    except Exception as e:
        print(f"Error inserting: {e}")
