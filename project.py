import requests
import os
import re
import msal
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TEST_GROUP_ID = os.getenv("TEST_GROUP_ID", "") 

# Microsoft Graph API endpoints
GRAPH_URL = "https://graph.microsoft.com/v1.0"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# Scopes for Application Permissions (always ends in /.default)
SCOPES = ["https://graph.microsoft.com/.default"]

def get_access_token_app():
    """Gets an access token via Client Secret (APPLICATION permissions)."""
    if not CLIENT_SECRET:
        raise Exception("CLIENT_SECRET not found in .env file")
        
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, 
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    # Try to get token from cache first
    result = app.acquire_token_silent(SCOPES, account=None)
    
    if not result:
        # Get a new token
        result = app.acquire_token_for_client(scopes=SCOPES)
    
    if "access_token" in result:
        return result["access_token"]
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
    """Fetches the unique User ID and name from a UPN."""
    if not upn: return None
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(f"{GRAPH_URL}/users/{upn}", headers=headers)
    if response.status_code == 200:
        return response.json()
    
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
    """Fetches all UPNs including nested group members (transitive)."""
    if not group_id:
        return set()

    headers = {'Authorization': f'Bearer {token}'}
    # Use transitiveMembers to expand nested groups
    endpoint = f"{GRAPH_URL}/groups/{group_id}/transitiveMembers?$select=userPrincipalName"

    upns = set()

    while endpoint:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()

        for member in data.get("value", []):
            upn = member.get("userPrincipalName")
            if upn:
                upns.add(upn.lower())

        # Handle pagination
        endpoint = data.get("@odata.nextLink")

    return upns

def send_teams_message(token, target_id, message_body):
    """Sends a message to a user using Application Permissions via BETA endpoint."""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    BETA_URL = "https://graph.microsoft.com/beta"
    
    # 1. Create a chat between the App and the User (Requires BETA for AppId member)
    chat_payload = {
        "chatType": "oneOnOne",
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadAppIdConversationMember",
                "roles": ["owner"],
                "appId": CLIENT_ID,
                "tenantId": TENANT_ID
            },
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"{GRAPH_URL}/users('{target_id}')"
            }
        ]
    }
    
    chat_res = requests.post(f"{BETA_URL}/chats", headers=headers, json=chat_payload)
    
    if chat_res.status_code in [200, 201]:
        chat_id = chat_res.json().get("id")
        msg_payload = {"body": {"contentType": "html", "content": message_body}}
        send_res = requests.post(f"{BETA_URL}/chats/{chat_id}/messages", headers=headers, json=msg_payload)
        return send_res.status_code == 201
    
    print(f"   [ERROR] Teams API Error: {chat_res.status_code} - {chat_res.text}")
    return False

def get_compliance_reasons(token, device_id):
    """Fetches the specific reasons (policies) why a device is non-compliant."""
    headers = {'Authorization': f'Bearer {token}'}
    endpoint = f"{GRAPH_URL}/deviceManagement/managedDevices('{device_id}')/deviceCompliancePolicyStates"
    
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            policies = response.json().get("value", [])
            failed_policies = [p.get('displayName') for p in policies if p.get('state') == 'nonCompliant']
            if failed_policies:
                return ", ".join(failed_policies)
    except Exception:
        pass
    return "Políticas de seguridad pendientes"

def main():
    try:
        print("Iniciando proceso en modo Servicio (Application Permissions)...")
        token = get_access_token_app()
        print("¡Autenticación de Aplicación exitosa!\n")

        print(f"Obteniendo miembros del grupo maestro: {TEST_GROUP_ID}")
        test_upns = get_group_member_upns(token, TEST_GROUP_ID)
        print(f"Total de usuarios en el alcance (incluyendo grupos anidados): {len(test_upns)}")
        
        devices = get_non_compliant_devices(token)

        if not devices:
            print("Todos los dispositivos están en regla.")
            return

        print(f"Encontrados {len(devices)} dispositivos non-compliant en el Tenant. Filtrando...\n")
        
        processed_count = 0
        for device in devices:
            device_id = device.get('id')
            device_name = device.get('deviceName', 'Unknown')
            raw_upn = (device.get('userPrincipalName') or "").lower()
            
            if TEST_GROUP_ID and (not raw_upn or raw_upn not in test_upns):
                continue

            processed_count += 1
            user_info = get_user_info(token, raw_upn)
            user_id = user_info.get('id') if user_info else None
            user_name = user_info.get('displayName', 'Usuario')
            
            compliance_reason = get_compliance_reasons(token, device_id)
            
            print(f"Procesando: {device_name} (Dueño: {user_name})")
            print(f"   Razón detectada: {compliance_reason}")

            trigger_remote_sync(token, device_id, device_name)
            
            if user_id:
                print(f"   [TEAMS] Enviando mensaje a {user_name}...")
                
                msg = (
                    f"🛡️ <b>Aviso de Ciberseguridad</b><br><br>"
                    f"Hola <b>{user_name}</b>, tu equipo <b>{device_name}</b> no cumple con las políticas de seguridad por: <b>{compliance_reason}</b>.<br><br>"
                    f"Hemos lanzado un sincronismo remoto. Por favor, mantén tu equipo conectado a internet para aplicar las correcciones automáticas."
                )
                
                if send_teams_message(token, user_id, msg):
                    print("   ¡Mensaje enviado con éxito!")
                else:
                    print("   Error al enviar el mensaje.")
            
            print("-" * 30)

        if processed_count == 0:
            print("No se encontraron dispositivos críticos dentro del alcance del grupo.")

    except Exception as e:
        print(f"Error Crítico: {e}")

if __name__ == "__main__":
    main()
