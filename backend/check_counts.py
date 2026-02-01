from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'postgresql://postgres:smxkwHcGTqHdwdcvePMPYLwxuQCRNrrU@yamabiko.proxy.rlwy.net:34388/railway'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

for uid in [16, 2]:
    count = session.execute(text('SELECT COUNT(*) FROM trades WHERE user_id = :id'), {'id': uid}).fetchone()[0]
    email = session.execute(text('SELECT email FROM users WHERE id = :id'), {'id': uid}).fetchone()[0]
    print(f'User {uid} ({email}): {count} trades')

session.close()
