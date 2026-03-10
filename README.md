# 🛡️ Cybersecurity bot for Microsoft Intune & Teams
[![Intune Compliance Bot](https://github.com/mriquelmec/Cybersecurity-Intune-Teams-Bot/actions/workflows/compliance.yml/badge.svg)](https://github.com/mriquelmec/Cybersecurity-Intune-Teams-Bot/actions/workflows/compliance.yml)

## Resumen del proyecto 

Este proyecto es una solución de ciberseguridad automatizada diseñada para organizaciones que utilizan **Microsoft Intune**. El bot identifica dispositivos que no cumplen con las políticas de cumplimiento (*Non-Compliant*), activa un **Sincronismo Remoto** para forzar la actualización de políticas y notifica proactivamente al usuario a través de un mensaje de **Microsoft Teams**.

### 🔄 Evolución: De script local a cloud automation
Originalmente, este proyecto nació como un script interactivo que requería autenticación manual del administrador (Device Code Flow). Para llevarlo a un entorno de **Producción Corporativa**, evolucionando eventualmente a una solución **Serverless** utilizando **GitHub Actions**.

*   **Sin Costo:** Corre 100% gratis en la infraestructura de GitHub.
*   **Sin Servidores:** No requiere una PC encendida; se ejecuta automáticamente cada 72 horas.
*   **Seguridad:** Utiliza Application Permissions (Client Secret) y secretos encriptados de GitHub.

---

## Project overview 

This project is an automated cybersecurity solution for organizations using **Microsoft Intune**. The bot scans for devices that are **Non-Compliant** with corporate security policies, triggers a **Remote Sync** to force policy updates, and proactively notifies the user via a **Microsoft Teams** message.

### 🔄 Evolution: from local script to cloud automation
Initially, this project started as an interactive script requiring manual administrator login (Device Code Flow). To reach **Enterprise Production** standards, it was evolved into a **Serverless** solution using **GitHub Actions**.

*   **Zero Cost:** Runs 100% free on GitHub’s infrastructure.
*   **Serverless:** No need for an always-on PC; it executes automatically every 72 hours.
*   **Security:** Implements Application Permissions (Client Secret) and GitHub Encrypted Secrets.

---

## 🛠️ Tech stack & architecture

*   **Python 3.10**: Core logic.
*   **Microsoft Graph API**: Interaction with Intune and Teams.
*   **MSAL (Microsoft Authentication Library)**: Secure authentication.
*   **GitHub Actions**: Cron-job scheduling and cloud execution.
*   **Microsoft Entra ID (Azure AD)**: App Registration with Application Permissions.

---

## 🚀 How to deploy / Cómo desplegar

### 1. Azure configuration (Entra ID)
1. Register an App in **Microsoft Entra ID**.
2. Add **Application Permissions** to Microsoft Graph:
   - `DeviceManagementManagedDevices.ReadWrite.All`
   - `User.Read.All`
   - `Chat.Create`
   - `ChatMessage.Send`
3. Grant **Admin Consent**.
4. Create a **Client Secret**.

### 2. GitHub setup
Go to your repository **Settings > Secrets and variables > Actions** and add:
- `TENANT_ID`
- `CLIENT_ID`
- `CLIENT_SECRET`
- `TEST_GROUP_ID` (Optional)

---

## 📁 Folder structure
- `project.py`: Main bot logic.
- `.github/workflows/compliance.yml`: Automation schedule.
- `requirements.txt`: Python dependencies.
- `.gitignore`: Ensures your `.env` and secrets are **never** public.

---
*Developed for Enterprise Cybersecurity Compliance.*
