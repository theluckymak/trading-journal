"""
Script to delete all users from Railway production database.
WARNING: This will permanently delete all users!
"""
import psycopg2
import os

# Railway database URL
# Get this from your Railway project environment variables
DATABASE_URL = "postgresql://postgres:WuZFfuQwAYjqZwxYRuPsuwPovAVWZkSi@junction.proxy.rlwy.net:27926/railway"

def delete_all_users():
    """Delete all users from the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("No users found in the database.")
            conn.close()
            return
        
        print(f"Found {user_count} user(s) in the Railway production database.")
        print("Deleting all users...")
        
        # Delete all trades first (foreign key constraint)
        cursor.execute("DELETE FROM trades WHERE user_id IN (SELECT id FROM users)")
        deleted_trades = cursor.rowcount
        
        # Delete all journal entries
        cursor.execute("DELETE FROM journal_entries WHERE user_id IN (SELECT id FROM users)")
        deleted_journals = cursor.rowcount
        
        # Delete all chat messages
        cursor.execute("DELETE FROM chat_messages WHERE user_id IN (SELECT id FROM users)")
        deleted_chats = cursor.rowcount
        
        # Delete all conversations
        cursor.execute("DELETE FROM conversations WHERE user_id IN (SELECT id FROM users)")
        deleted_conversations = cursor.rowcount
        
        # Now delete users
        cursor.execute("DELETE FROM users")
        
        conn.commit()
        
        print(f"✓ Successfully deleted:")
        print(f"  - {user_count} user(s)")
        print(f"  - {deleted_trades} trade(s)")
        print(f"  - {deleted_journals} journal entry(ies)")
        print(f"  - {deleted_chats} chat message(s)")
        print(f"  - {deleted_conversations} conversation(s)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error deleting users: {str(e)}")
        raise

if __name__ == "__main__":
    delete_all_users()
