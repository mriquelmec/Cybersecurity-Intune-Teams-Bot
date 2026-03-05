import os
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = [
    "User.Read", 
    "GroupMember.Read.All", 
    "DeviceManagementManagedDevices.ReadWrite.All",
    "Chat.Create",
    "Chat.ReadWrite"
]

def get_code():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print(f"Error: {flow.get('error_description')}")
        return
    
    print(f"CODE: {flow['user_code']}")
    print(f"URL: {flow['verification_uri']}")

if __name__ == "__main__":
    get_code()
