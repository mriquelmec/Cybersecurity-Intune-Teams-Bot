import requests
import os
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID")

def test_permissions():
    payload = {
        'client_id': CLIENT_ID,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_response = requests.post(token_url, data=payload)
    if token_response.status_code != 200:
        print(f"Token Error: {token_response.status_code} - {token_response.text}")
        return
    
    token = token_response.json().get("access_token")
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Testing access to group: {TEST_GROUP_ID}")
    
    # Test 1: Get Group Info
    res1 = requests.get(f"https://graph.microsoft.com/v1.0/groups/{TEST_GROUP_ID}", headers=headers)
    print(f"1. Get Group details: {res1.status_code}")
    if res1.status_code != 200:
        print(f"   Reason: {res1.text}")

    # Test 2: Get Group Members
    res2 = requests.get(f"https://graph.microsoft.com/v1.0/groups/{TEST_GROUP_ID}/members", headers=headers)
    print(f"2. Get Group members: {res2.status_code}")
    if res2.status_code != 200:
        print(f"   Reason: {res2.text}")

    # Test 3: List Managed Devices
    res3 = requests.get("https://graph.microsoft.com/v1.0/deviceManagement/managedDevices", headers=headers)
    print(f"3. List Managed Devices: {res3.status_code}")
    if res3.status_code != 200:
        print(f"   Reason: {res3.text}")

if __name__ == "__main__":
    test_permissions()
