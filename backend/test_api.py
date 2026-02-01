"""Test the chat API directly"""
import requests

API_URL = "https://dependable-solace-production-75f7.up.railway.app"

# First login to get a token
login_resp = requests.post(f"{API_URL}/api/auth/login", json={
    "email": "yassinkaltoum83@gmail.com",
    "password": "Test123!"  # Replace with actual password
})

print(f"Login status: {login_resp.status_code}")
if login_resp.status_code == 200:
    tokens = login_resp.json()
    access_token = tokens.get("access_token")
    print(f"Got token: {access_token[:20]}...")
    
    # Get user info
    me_resp = requests.get(f"{API_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {access_token}"
    })
    print(f"Me status: {me_resp.status_code}")
    if me_resp.status_code == 200:
        user = me_resp.json()
        print(f"User: {user}")
    
    # Try to send a message
    msg_resp = requests.post(f"{API_URL}/api/chat/messages", 
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "message": "Test message from script",
            "conversation_user_id": 16
        }
    )
    print(f"\nSend message status: {msg_resp.status_code}")
    print(f"Response: {msg_resp.text}")
else:
    print(f"Login failed: {login_resp.text}")
