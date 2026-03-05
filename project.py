import requests
import os
import re
import msal
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID", "") 

# Microsoft Graph API endpoints
GRAPH_URL = "https://graph.microsoft.com/v1.0"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Scopes required for Delegated (User) access
SCOPES = [
    "User.Read", 
    "User.ReadBasic.All",
    "GroupMember.Read.All", 
    "DeviceManagementManagedDevices.ReadWrite.All",
    "Chat.Create",
    "Chat.ReadWrite"
]

def get_access_token_delegated():
    """Gets an access token via Device Code Flow (DELEGATED permissions)."""
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception(f"Could not initiate device flow: {flow.get('error_description')}")
    
    print("\n" + "=" * 60)
    print(f" AUTENTICACIÓN REQUERIDA ")
    print(f" 1. Ve a: {flow['verification_uri']}")
    print(f" 2. Introduce el código: {flow['user_code']}")
    print("=" * 60 + "\n")
    
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        # Get the current user's ID from the token claims
        user_id = result.get('id_token_claims', {}).get('oid')
        return result["access_token"], user_id
    else:
        raise Exception(f"Authentication failed: {result.get('error_description')}")

def get_non_compliant_devices(token):
    """Fetches a list of devices that are non-compliant in Intune."""
    headers = {'Authorization': f'Bearer {token}'}
    endpoint = f"{GRAPH_URL}/deviceManagement/managedDevices?$filter=complianceState eq 'noncompliant'"
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])

def get_user_info(token, upn):
    """Fetches the unique User ID and name from a UPN, handling encrypted formats."""
    if not upn: return None
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try direct lookup
    response = requests.get(f"{GRAPH_URL}/users/{upn}", headers=headers)
    if response.status_code == 200:
        return response.json()
    
    # Try searching by extracted email if UPN is messy
    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", upn)
    if email_match:
        email = email_match.group(1)
        search_res = requests.get(f"{GRAPH_URL}/users?$filter=mail eq '{email}' or userPrincipalName eq '{email}'", headers=headers)
        if search_res.status_code == 200:
            results = search_res.json().get("value", [])
            if results: return results[0]
                
    return None

def trigger_remote_sync(token, device_id, device_name):
    """Triggers a remote 'Sync' action on a specific device."""
    headers = {'Authorization': f'Bearer {token}'}
    endpoint = f"{GRAPH_URL}/deviceManagement/managedDevices('{device_id}')/syncDevice"
    
    print(f"   [SYNC] Triggering for: {device_name}...")
    response = requests.post(endpoint, headers=headers)
    if response.status_code == 204:
        print(f"   Success! Sync command sent.")
    else:
        print(f"   Notice: Sync failed (Status: {response.status_code}).")

def get_group_member_upns(token, group_id):
    """Fetches all User Principal Names (UPNs) that are members of the specified group."""
    if not group_id: return set()
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{GRAPH_URL}/groups/{group_id}/members?$select=userPrincipalName", headers=headers)
    if response.status_code == 200:
        return {m.get('userPrincipalName').lower() for m in response.json().get("value", []) if m.get('userPrincipalName')}
    return set()

def send_teams_message(token, my_id, target_id, message_body):
    """Sends a 1-on-1 Teams message as the logged-in user."""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    if my_id == target_id:
        print("   [INFO] Recipient is you. Skipping message.")
        return True

    # 1. Ensure a 1-on-1 chat exists
    chat_payload = {
        "chatType": "oneOnOne",
        "members": [
            {"@odata.type": "#microsoft.graph.aadUserConversationMember", "roles": ["owner"], "user@odata.bind": f"{GRAPH_URL}/users('{my_id}')"},
            {"@odata.type": "#microsoft.graph.aadUserConversationMember", "roles": ["owner"], "user@odata.bind": f"{GRAPH_URL}/users('{target_id}')"}
        ]
    }
    
    chat_res = requests.post(f"{GRAPH_URL}/chats", headers=headers, json=chat_payload)
    
    if chat_res.status_code in [200, 201]:
        chat_id = chat_res.json().get("id")
        # 2. Send the message
        msg_payload = {"body": {"contentType": "html", "content": message_body}}
        send_res = requests.post(f"{GRAPH_URL}/chats/{chat_id}/messages", headers=headers, json=msg_payload)
        return send_res.status_code == 201
    
    print(f"   [ERROR] Could not create chat: {chat_res.text}")
    return False

def main():
    try:
        print("Iniciando proceso con Autenticación de Usuario (Delegated)...")
        token, my_user_id = get_access_token_delegated()
        print(f"¡Autenticado con éxito!\n")

        test_upns = get_group_member_upns(token, TEST_GROUP_ID)
        devices = get_non_compliant_devices(token)

        if not devices:
            print("Todos los dispositivos están en regla.")
            return

        print(f"Encontrados {len(devices)} dispositivos non-compliant. Procesando...\n")
        
        processed_count = 0
        for device in devices:
            device_name = device.get('deviceName', 'Unknown')
            raw_upn = (device.get('userPrincipalName') or "").lower()
            
            # Filter by group if ID is provided
            if TEST_GROUP_ID and (not raw_upn or raw_upn not in test_upns):
                continue

            processed_count += 1
            user_info = get_user_info(token, raw_upn)
            user_id = user_info.get('id') if user_info else None
            user_name = user_info.get('displayName', 'Usuario')
            
            print(f"Procesando: {device_name} (Dueño: {user_name})")

            trigger_remote_sync(token, device.get('id'), device_name)
            
            if user_id:
                print(f"   [TEAMS] Enviando mensaje a {user_name}...")
                msg = f"Hola <b>{user_name}</b>!<br><br>Tu dispositivo <b>{device_name}</b> no cumple con las políticas de seguridad.<br>Hemos activado un <b>Sincronismo Remoto</b>. Por favor, abre la app <b>Portal de Empresa</b>."
                
                if send_teams_message(token, my_user_id, user_id, msg):
                    print("   ¡Mensaje enviado con éxito!")
                else:
                    print("   Error al enviar el mensaje.")
            else:
                print(f"   [WARNING] No se pudo obtener el User ID para {raw_upn}. No se envió mensaje de Teams.")
            
            print("-" * 30)

        if processed_count == 0:
            print("No se encontraron dispositivos para usuarios en el grupo de prueba.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
