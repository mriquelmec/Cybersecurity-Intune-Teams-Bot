# Cybersecurity Compliance Bot for Teams & Intune

This project automates the notification of non-compliant devices in Microsoft Intune via Microsoft Teams. It identifies devices that do not meet security policies, triggers a remote sync, and sends a personalized message to the device owner.

## Features

- **Intune Compliance Check**: Fetches a list of non-compliant devices using Microsoft Graph API.
- **Remote Sync**: Automatically triggers a remote sync action on non-compliant devices.
- **Teams Notifications**: Sends 1-on-1 Teams messages to users with non-compliant devices.
- **Group Filtering**: Optional filtering to only process users within a specific Entra ID (Azure AD) group.

## Prerequisites

- Python 3.x
- An Entra ID (Azure AD) App Registration with the following Delegated permissions:
  - `User.Read`
  - `User.ReadBasic.All`
  - `GroupMember.Read.All`
  - `DeviceManagementManagedDevices.ReadWrite.All`
  - `Chat.Create`
  - `Chat.ReadWrite`

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```env
   TENANT_ID=your_tenant_id
   CLIENT_ID=your_client_id
   TEST_GROUP_ID=your_test_group_id (optional)
   ```

## Usage

Run the main script:
```bash
python project.py
```

Follow the on-screen instructions for Device Code authentication.

## Project Structure

- `project.py`: Main logic for device compliance and notifications.
- `tests/`: Directory containing diagnostic and test scripts.
- `.env`: (Ignored) Configuration for sensitive credentials.

## Future Plans

- Transition to a Teams App Bot for automated production use.
- Integration with Intune App protection policies.
