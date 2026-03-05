import requests
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID")

def get_app_token():
    payload = {
        'client_id': CLIENT_ID,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    res = requests.post(token_url, data=payload)
    res.raise_for_status()
    return res.json().get("access_token")

def test_app_message():
    try:
        token = get_app_token()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # 1. Get a user from the test group
        members_res = requests.get(f"https://graph.microsoft.com/v1.0/groups/{TEST_GROUP_ID}/members?$select=id,displayName", headers=headers)
        members_res.raise_for_status()
        members = members_res.json().get("value", [])
        
        if len(members) < 2:
            print("Need at least 2 members in test group to create a 1-on-1 chat.")
            return

        recipient = members[0]
        sender = members[1]
        print(f"Attempting to send message from {sender['displayName']} to {recipient['displayName']}")

        # 2. Create or find chat (Application context with Teamwork.Migrate.All)
        chat_payload = {
            "chatType": "oneOnOne",
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{recipient['id']}')"
                },
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{sender['id']}')"
                }
            ]
        }
        
        # Let's try to create a chat with just the recipient (some APIs allow this for bot chats)
        # Or specify a sender if we want to impersonate (migration flow)
        # For now, let's see if we can create a chat.
        
        print("Creating chat...")
        chat_res = requests.post("https://graph.microsoft.com/v1.0/chats", headers=headers, json=chat_payload)
        
        if chat_res.status_code not in [200, 201]:
            print(f"Chat Creation failed: {chat_res.status_code} - {chat_res.text}")
            return
            
        chat_id = chat_res.json().get("id")
        print(f"Chat ID: {chat_id}")

        # 3. Send message
        msg_payload = {
            "body": {
                "contentType": "html",
                "content": "<b>Test App Notification</b>: Access verified with Teamwork.Migrate.All."
            }
        }
        msg_res = requests.post(f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages", headers=headers, json=msg_payload)
        
        if msg_res.status_code == 201:
            print("Success! Message sent using Application permissions.")
        else:
            print(f"Message failed: {msg_res.status_code} - {msg_res.text}")

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_app_message()
