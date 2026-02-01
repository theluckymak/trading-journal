"""Test sending a chat message"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

DATABASE_URL = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Find admin user
admin = session.execute(text("SELECT id, email, role FROM users WHERE role = 'ADMIN' LIMIT 1")).fetchone()
print(f"Admin: {admin}")

# Find regular user
regular = session.execute(text("SELECT id, email FROM users WHERE role != 'ADMIN' LIMIT 1")).fetchone()
print(f"Regular user: {regular}")

if admin and regular:
    # Test insert from admin to user
    try:
        session.execute(text("""
            INSERT INTO chat_messages (user_id, conversation_user_id, message, is_admin, created_at)
            VALUES (:user_id, :conversation_user_id, :message, :is_admin, :created_at)
        """), {
            "user_id": admin[0],
            "conversation_user_id": regular[0],
            "message": "Test message from admin",
            "is_admin": True,
            "created_at": datetime.now(timezone.utc)
        })
        session.commit()
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()

# Count messages
count = session.execute(text("SELECT COUNT(*) FROM chat_messages")).fetchone()[0]
print(f"Total messages in database: {count}")

session.close()
