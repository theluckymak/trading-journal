"""Check user roles"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get all users with their roles
result = session.execute(text("SELECT id, email, role FROM users ORDER BY id"))
print("Users and roles:")
for row in result:
    print(f"  User {row[0]}: {row[1]} - role: '{row[2]}'")

session.close()
