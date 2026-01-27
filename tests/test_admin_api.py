import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_admin_api(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing Admin API at {BASE_URL}/admin/users...")
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"Successfully fetched {len(users)} users.")
        if users:
            print("First user preview:", users[0])
    else:
        print("Error Response:", response.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_admin_api.py <JWT_TOKEN>")
        sys.exit(1)
        
    test_admin_api(sys.argv[1])
