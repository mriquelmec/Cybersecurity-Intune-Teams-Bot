import requests
import os
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID")
GRAPH_URL = "https://graph.microsoft.com/v1.0"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["User.Read", "GroupMember.Read.All", "DeviceManagementManagedDevices.ReadWrite.All"]

def get_token():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result: return result["access_token"]
    
    flow = app.initiate_device_flow(scopes=SCOPES)
    print(f"Auth required: {flow['message']}")
    result = app.acquire_token_by_device_flow(flow)
    return result.get("access_token")

def debug():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    target_upn = os.getenv("TARGET_UPN", "user@example.com")
    print(f"\n--- Finding User ID for: {target_upn} ---")
    res = requests.get(f"{GRAPH_URL}/users/{target_upn}", headers=headers)
    target_user_id = None
    if res.status_code == 200:
        target_user_id = res.json().get('id')
        print(f"User ID for {target_upn} is: {target_user_id}")
    else:
        print(f"Could not find user {target_upn}: {res.text}")

    group_ids = [os.getenv("TEST_GROUP_ID")]
    group_ids = list(set(gid for gid in group_ids if gid))

    for gid in group_ids:
        print(f"\n--- Checking Group Members for Group ID: {gid} ---")
        res = requests.get(f"{GRAPH_URL}/groups/{gid}/members?$select=id,userPrincipalName,displayName", headers=headers)
        if res.status_code != 200:
            print(f"Error fetching group {gid}: {res.text}")
            continue
        members = res.json().get("value", [])
        is_member = False
        for m in members:
            mid = m.get('id')
            mupn = m.get('userPrincipalName')
            print(f"Member: {mupn} (ID: {mid}, Name: {m.get('displayName')})")
            if target_user_id and mid == target_user_id:
                is_member = True
        print(f"RESULT: User {target_upn} IS {'IN' if is_member else 'NOT IN'} group {gid}")

    print(f"\n--- Searching for Device ---")
    device_name_to_search = os.getenv("TARGET_DEVICE_NAME", "Unknown")
    res = requests.get(f"{GRAPH_URL}/deviceManagement/managedDevices?$filter=deviceName eq '{device_name_to_search}'", headers=headers)
    devices = res.json().get("value", [])
    for d in devices:
        print(f"Device: {d.get('deviceName')} | Status: {d.get('complianceState')} | UPN: {d.get('userPrincipalName')}")

if __name__ == "__main__":
    debug()
