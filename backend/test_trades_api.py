"""Test trades API directly."""
import requests

API_URL = "https://dependable-solace-production-75f7.up.railway.app"

# First login to get a token
print("Testing login...")
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={
        "email": "yassinkaltoum83@gmail.com",
        "password": "test123"  # You may need to update this
    },
    timeout=30
)

print(f"Login status: {login_response.status_code}")
if login_response.status_code == 200:
    tokens = login_response.json()
    access_token = tokens.get("access_token")
    print(f"Got token: {access_token[:20]}...")
    
    # Now fetch trades
    print("\nFetching trades...")
    trades_response = requests.get(
        f"{API_URL}/api/trades",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": 10},
        timeout=30
    )
    
    print(f"Trades status: {trades_response.status_code}")
    if trades_response.status_code == 200:
        trades = trades_response.json()
        print(f"Found {len(trades)} trades")
        for trade in trades[:5]:
            print(f"  - {trade.get('symbol')} {trade.get('trade_type')} profit={trade.get('profit')}")
    else:
        print(f"Error: {trades_response.text}")
else:
    print(f"Login failed: {login_response.text}")
