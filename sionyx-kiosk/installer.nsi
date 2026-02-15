; SIONYX Installer Script for NSIS
; This creates a professional Windows installer with integrated kiosk setup

!define APP_NAME "SIONYX"
; VERSION is passed from build.py via /DVERSION="x.y.z"
; Fallback to 0.0.0 if not provided (manual NSIS compile)
!ifndef VERSION
    !define VERSION "0.0.0"
!endif
!define APP_PUBLISHER "SIONYX Technologies"
!define APP_URL "https://sionyx.app"
!define APP_EXECUTABLE "SIONYX.exe"
!define APP_ICON "app-logo.ico"
!define INSTALLER_NAME "SIONYX-Installer.exe"
!define KIOSK_USERNAME "KioskUser"

; Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"

; Variables
Var OrgNameInput
Var OrgNameText
Var BigFont
Var MediumFont

; General
Name "${APP_NAME}"
OutFile "${INSTALLER_NAME}"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
Page custom OrgPagePre OrgPageLeave          ; Organization name page
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; INSTALLER SECTION - Main Application
; ============================================================================
Section "Main Application" SecMain
    ; IMPORTANT: Force 64-bit registry view so keys are written to native
    ; HKLM\SOFTWARE\SIONYX instead of WOW6432Node (which 64-bit apps can't read)
    SetRegView 64
    
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "${APP_EXECUTABLE}"
    
    ; Copy application icon
    File "${APP_ICON}"
    
    ; =========================================================================
    ; Store ALL configuration in Windows Registry
    ; This replaces .env file for production builds
    ; =========================================================================
    
    ; Installation info
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "Version" "${VERSION}"
    
    ; Organization Configuration
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "OrgId" "$OrgNameText"
    
    ; Firebase Configuration
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseApiKey" "AIzaSyDS5hMOBeo1WtZdzP4L0WtpzLL0gI-S0-c"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseAuthDomain" "sionyx-19636.firebaseapp.com"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseProjectId" "sionyx-19636"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseDatabaseUrl" "https://sionyx-19636-default-rtdb.europe-west1.firebasedatabase.app"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseStorageBucket" "sionyx-19636.firebasestorage.app"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseMessagingSenderId" "961130757239"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseAppId" "1:961130757239:web:1a87dffcea40aac13f1a72"
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "FirebaseMeasurementId" "G-ZEM9LH1301"
    
    ; Payment Gateway Configuration
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "NedarimCallbackUrl" "https://us-central1-sionyx-19636.cloudfunctions.net/nedarimCallback"
    
    ; Security - Admin exit password (change this per deployment)
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "AdminExitPassword" "sionyx2025"
    
    DetailPrint "[OK] Configuration stored in Windows Registry"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Add to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" '"$INSTDIR\${APP_ICON}"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Create desktop shortcut with icon (for admin use)
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_ICON}" 0
    
    ; Create start menu shortcut with icon
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_ICON}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
SectionEnd

; ============================================================================
; KIOSK SETUP SECTION - Creates restricted user and applies security
; ============================================================================
Section "Kiosk Security Setup" SecKiosk
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  STEP 1: Creating Kiosk User Account"
    DetailPrint "============================================"
    DetailPrint ""
    DetailPrint "Creating a restricted Windows user account..."
    DetailPrint "This account will be used by customers at the kiosk."
    DetailPrint "(No password required - SIONYX app handles authentication)"
    DetailPrint ""
    
    ; Enable blank password logon (required for passwordless account)
    DetailPrint "[CONFIG] Enabling blank password logon..."
    nsExec::ExecToLog 'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d 0 /f'
    Pop $0
    
    ; Create KioskUser account using net user (simpler and more reliable than PowerShell)
    ; First check if user exists
    DetailPrint "[CHECK] Looking for existing user '${KIOSK_USERNAME}'..."
    nsExec::ExecToLog 'net user "${KIOSK_USERNAME}"'
    Pop $0
    
    ${If} $0 == 0
        DetailPrint "[INFO] User '${KIOSK_USERNAME}' already exists - removing password..."
        ; Set blank password for existing user
        nsExec::ExecToLog 'net user "${KIOSK_USERNAME}" ""'
        Pop $0
        ${If} $0 != 0
            DetailPrint "[WARNING] Could not remove password, continuing..."
        ${EndIf}
    ${Else}
        DetailPrint "[CREATING] New user account '${KIOSK_USERNAME}' (no password)..."
        ; Create user with blank password
        nsExec::ExecToLog 'net user "${KIOSK_USERNAME}" "" /add /fullname:"SIONYX Kiosk User" /comment:"Restricted kiosk account for SIONYX" /passwordchg:no'
        Pop $0
        ${If} $0 != 0
            DetailPrint "[ERROR] Failed to create user account! Error code: $0"
            MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to create KioskUser account.$\n$\nError code: $0$\n$\nPlease contact support."
            Abort
        ${EndIf}
        
        ; Ensure password never expires
        DetailPrint "[CONFIG] Setting password to never expire..."
        nsExec::ExecToLog 'wmic useraccount where name="${KIOSK_USERNAME}" set PasswordExpires=false'
        Pop $0
    ${EndIf}
    
    ; Verify user was created
    DetailPrint "[VERIFY] Checking user account exists..."
    nsExec::ExecToLog 'net user "${KIOSK_USERNAME}"'
    Pop $0
    ${If} $0 != 0
        DetailPrint "[ERROR] User verification failed!"
        MessageBox MB_OK|MB_ICONEXCLAMATION "KioskUser account was not created.$\n$\nThe user creation command ran but the user doesn't exist.$\nThis is unusual - please check Windows Event Viewer for details."
        Abort
    ${EndIf}
    DetailPrint "[OK] User '${KIOSK_USERNAME}' verified!"
    
    ; Make sure user is NOT an administrator (remove from Administrators group if somehow added)
    DetailPrint "[SECURITY] Ensuring user has limited permissions (not administrator)..."
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "Remove-LocalGroupMember -Group ''Administrators'' -Member ''${KIOSK_USERNAME}'' -ErrorAction SilentlyContinue"'
    Pop $0
    
    ; Add user to Users group
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "Add-LocalGroupMember -Group ''Users'' -Member ''${KIOSK_USERNAME}'' -ErrorAction SilentlyContinue"'
    Pop $0
    
    DetailPrint "[OK] Kiosk user account ready!"
    DetailPrint ""
    
    ; ========================================================================
    DetailPrint "============================================"
    DetailPrint "  STEP 2: Applying Security Restrictions"
    DetailPrint "============================================"
    DetailPrint ""
    DetailPrint "Configuring Windows to prevent unauthorized access..."
    DetailPrint "This blocks dangerous tools that customers shouldn't use."
    DetailPrint ""
    
    ; Create PowerShell script to apply registry restrictions
    FileOpen $0 "$TEMP\sionyx_kiosk_setup.ps1" w
    FileWrite $0 '# SIONYX Kiosk Registry Restrictions$\r$\n'
    FileWrite $0 '# This script applies security restrictions to the KioskUser account$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '$$username = "${KIOSK_USERNAME}"$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Get user SID$\r$\n'
    FileWrite $0 '$$user = Get-LocalUser -Name $$username -ErrorAction SilentlyContinue$\r$\n'
    FileWrite $0 'if (-not $$user) { Write-Host "[ERROR] User not found"; exit 1 }$\r$\n'
    FileWrite $0 '$$userSID = $$user.SID.Value$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Create user profile if it does not exist (force profile creation)$\r$\n'
    FileWrite $0 '$$profilePath = "C:\Users\$$username"$\r$\n'
    FileWrite $0 'if (-not (Test-Path $$profilePath)) {$\r$\n'
    FileWrite $0 '    Write-Host "[INFO] Creating user profile folder..."$\r$\n'
    FileWrite $0 '    New-Item -Path $$profilePath -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Apply restrictions via HKLM (affects all users but we target via Group Policy)$\r$\n'
    FileWrite $0 '# These are machine-wide policies that will apply to standard users$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Create policy paths$\r$\n'
    FileWrite $0 '$$explorerPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"$\r$\n'
    FileWrite $0 '$$systemPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 'if (-not (Test-Path $$explorerPath)) { New-Item -Path $$explorerPath -Force | Out-Null }$\r$\n'
    FileWrite $0 'if (-not (Test-Path $$systemPath)) { New-Item -Path $$systemPath -Force | Out-Null }$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Restriction: Disable Run dialog (Win+R)$\r$\n'
    FileWrite $0 'Write-Host "[APPLYING] Disabling Run dialog (Win+R)..."$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$explorerPath -Name "NoRun" -Value 1 -Type DWord -Force$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Restriction: Disable Registry Editor$\r$\n'
    FileWrite $0 'Write-Host "[APPLYING] Blocking Registry Editor..."$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableRegistryTools" -Value 1 -Type DWord -Force$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Restriction: Disable Command Prompt$\r$\n'
    FileWrite $0 'Write-Host "[APPLYING] Blocking Command Prompt..."$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableCMD" -Value 2 -Type DWord -Force$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Restriction: Disable Task Manager (for non-admin users)$\r$\n'
    FileWrite $0 'Write-Host "[APPLYING] Blocking Task Manager..."$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableTaskMgr" -Value 1 -Type DWord -Force$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Store kiosk username for uninstaller$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path "HKLM:\SOFTWARE\${APP_NAME}" -Name "KioskUser" -Value $$username -Type String -Force$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 'Write-Host "[OK] All security restrictions applied!"$\r$\n'
    FileClose $0
    
    ; Execute the PowerShell script
    DetailPrint "[APPLYING] Disabling Run dialog (Win+R)..."
    DetailPrint "[APPLYING] Blocking Registry Editor..."
    DetailPrint "[APPLYING] Blocking Command Prompt..."
    DetailPrint "[APPLYING] Blocking Task Manager..."
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_kiosk_setup.ps1"'
    Pop $0
    
    ; Clean up temp script
    Delete "$TEMP\sionyx_kiosk_setup.ps1"
    
    DetailPrint "[OK] Security restrictions applied!"
    DetailPrint ""
    
    ; ========================================================================
    DetailPrint "============================================"
    DetailPrint "  STEP 3: Setting Up Auto-Start"
    DetailPrint "============================================"
    DetailPrint ""
    DetailPrint "Configuring SIONYX to start automatically when the"
    DetailPrint "kiosk user logs in. This ensures the kiosk is always"
    DetailPrint "ready for customers."
    DetailPrint ""
    
    ; NOTE: We use MULTIPLE methods to ensure auto-start works reliably:
    ; 1. Scheduled Task (works even if profile doesn't exist yet)
    ; 2. Startup folder shortcut (created when profile exists or on first login)
    ; 3. Registry Run key for KioskUser (as fallback)
    
    ; =========================================================================
    ; METHOD 1: Scheduled Task (primary, most reliable)
    ; =========================================================================
    DetailPrint "[AUTOSTART] Creating scheduled task for KioskUser..."
    
    ; Delete any existing task first to ensure clean state
    nsExec::ExecToLog 'schtasks /delete /tn "SIONYX Kiosk" /f'
    
    ; Create PowerShell script for scheduled task (more control over settings)
    FileOpen $1 "$TEMP\create_sionyx_task.ps1" w
    FileWrite $1 '# Create SIONYX Kiosk scheduled task$\r$\n'
    FileWrite $1 '$$ErrorActionPreference = "Stop"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '$$exePath = "$INSTDIR\${APP_EXECUTABLE}"$\r$\n'
    FileWrite $1 '$$taskName = "SIONYX Kiosk"$\r$\n'
    FileWrite $1 '$$userName = "${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Create action - run SIONYX in kiosk mode$\r$\n'
    FileWrite $1 '$$action = New-ScheduledTaskAction -Execute $$exePath -Argument "--kiosk"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Trigger on logon of KioskUser$\r$\n'
    FileWrite $1 '$$trigger = New-ScheduledTaskTrigger -AtLogOn -User $$userName$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Settings - ensure it runs reliably$\r$\n'
    FileWrite $1 '$$settings = New-ScheduledTaskSettingsSet `$\r$\n'
    FileWrite $1 '    -AllowStartIfOnBatteries `$\r$\n'
    FileWrite $1 '    -DontStopIfGoingOnBatteries `$\r$\n'
    FileWrite $1 '    -StartWhenAvailable `$\r$\n'
    FileWrite $1 '    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `$\r$\n'
    FileWrite $1 '    -RestartCount 3 `$\r$\n'
    FileWrite $1 '    -RestartInterval (New-TimeSpan -Minutes 1)$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Principal - run as KioskUser interactively$\r$\n'
    FileWrite $1 '$$principal = New-ScheduledTaskPrincipal `$\r$\n'
    FileWrite $1 '    -UserId $$userName `$\r$\n'
    FileWrite $1 '    -LogonType Interactive `$\r$\n'
    FileWrite $1 '    -RunLevel Limited$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Register the task$\r$\n'
    FileWrite $1 'Register-ScheduledTask `$\r$\n'
    FileWrite $1 '    -TaskName $$taskName `$\r$\n'
    FileWrite $1 '    -Action $$action `$\r$\n'
    FileWrite $1 '    -Trigger $$trigger `$\r$\n'
    FileWrite $1 '    -Settings $$settings `$\r$\n'
    FileWrite $1 '    -Principal $$principal `$\r$\n'
    FileWrite $1 '    -Force$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 'Write-Host "[OK] Scheduled task created successfully"$\r$\n'
    FileClose $1
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\create_sionyx_task.ps1"'
    Pop $0
    Delete "$TEMP\create_sionyx_task.ps1"
    
    ${If} $0 == 0
        DetailPrint "[OK] Scheduled task created successfully"
    ${Else}
        DetailPrint "[WARNING] Scheduled task creation failed (error $0)"
    ${EndIf}
    
    ; =========================================================================
    ; METHOD 2: Startup folder shortcut (fallback)
    ; =========================================================================
    DetailPrint "[AUTOSTART] Creating startup folder shortcut..."
    
    ; Check if KioskUser profile exists
    IfFileExists "C:\Users\${KIOSK_USERNAME}\*.*" 0 create_profile_first
    
    ; Profile exists - create startup shortcut directly
    CreateDirectory "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    CreateShortCut "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXECUTABLE}" "--kiosk" "$INSTDIR\${APP_ICON}" 0
    DetailPrint "[OK] Startup shortcut created for KioskUser"
    Goto autostart_done
    
    create_profile_first:
    ; Profile doesn't exist yet - create it and the startup shortcut
    DetailPrint "[INFO] KioskUser profile doesn't exist yet, creating..."
    
    ; Force profile creation by running a command as the user
    ; This creates the basic profile structure
    FileOpen $1 "$TEMP\create_profile.ps1" w
    FileWrite $1 '# Force create KioskUser profile$\r$\n'
    FileWrite $1 '$$username = "${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 '$$profilePath = "C:\Users\$$username"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Create profile directories$\r$\n'
    FileWrite $1 '$$startupPath = "$$profilePath\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"$\r$\n'
    FileWrite $1 'New-Item -Path $$startupPath -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Create .sionyx directory$\r$\n'
    FileWrite $1 'New-Item -Path "$$profilePath\.sionyx" -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Create Local AppData SIONYX directory$\r$\n'
    FileWrite $1 'New-Item -Path "$$profilePath\AppData\Local\SIONYX\logs" -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 'Write-Host "[OK] Profile directories created"$\r$\n'
    FileClose $1
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\create_profile.ps1"'
    Pop $0
    Delete "$TEMP\create_profile.ps1"
    
    ; Now create the startup shortcut
    CreateShortCut "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXECUTABLE}" "--kiosk" "$INSTDIR\${APP_ICON}" 0
    DetailPrint "[OK] Startup shortcut created for KioskUser"
    
    autostart_done:
    
    ; Store kiosk username in registry for reference
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "KioskUsername" "${KIOSK_USERNAME}"
    DetailPrint "[OK] Stored kiosk username in registry"
    DetailPrint "[INFO] SIONYX will auto-start ONLY for ${KIOSK_USERNAME}"
    
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  SETUP COMPLETE!"
    DetailPrint "============================================"
    DetailPrint ""
    DetailPrint "Your kiosk is now configured and secure."
    DetailPrint ""
    DetailPrint "NEXT STEPS:"
    DetailPrint "1. Log out of your admin account"
    DetailPrint "2. Log in as '${KIOSK_USERNAME}'"
    DetailPrint "3. SIONYX will start automatically"
    DetailPrint ""
    DetailPrint "REMEMBER: Keep your admin password safe!"
    DetailPrint "You will need it to make changes or uninstall."
    DetailPrint ""
SectionEnd

; ============================================================================
; UNINSTALLER SECTION
; ============================================================================
Section "Uninstall"
    ; Use 64-bit registry view to match installation
    SetRegView 64
    
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  Removing SIONYX Application"
    DetailPrint "============================================"
    DetailPrint ""
    
    ; Remove program files
    DetailPrint "[CLEANUP] Removing program files..."
    Delete "$INSTDIR\${APP_EXECUTABLE}"
    Delete "$INSTDIR\${APP_ICON}"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\web"
    RMDir /r "$INSTDIR\templates"
    RMDir /r "$INSTDIR\_internal"
    
    ; Remove shortcuts
    DetailPrint "[CLEANUP] Removing shortcuts..."
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove auto-start entries
    DetailPrint "[CLEANUP] Removing auto-start entries..."
    ; Remove scheduled task (primary method)
    nsExec::ExecToLog 'schtasks /delete /tn "SIONYX Kiosk" /f'
    
    ; Clean up old entries from previous installations
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
    SetShellVarContext all
    Delete "$SMSTARTUP\${APP_NAME}.lnk"
    SetShellVarContext current
    
    ; Remove KioskUser startup shortcut (legacy cleanup)
    Delete "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    
    ; Remove from Default profile (if we used that method)
    Delete "C:\Users\Default\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    
    ; =========================================================================
    ; CLEANUP SIONYX APPLICATION DATA (for all users)
    ; This ensures a fresh start on reinstall
    ; =========================================================================
    DetailPrint ""
    DetailPrint "[CLEANUP] Removing SIONYX application data..."
    
    ; Remove current user's SIONYX data
    ; ~/.sionyx folder (contains auth.db with encrypted tokens)
    RMDir /r "$PROFILE\.sionyx"
    
    ; %LOCALAPPDATA%\SIONYX folder (contains logs)
    RMDir /r "$LOCALAPPDATA\${APP_NAME}"
    
    ; Remove KioskUser's SIONYX data
    RMDir /r "C:\Users\${KIOSK_USERNAME}\.sionyx"
    RMDir /r "C:\Users\${KIOSK_USERNAME}\AppData\Local\${APP_NAME}"
    
    ; =========================================================================
    ; CLEANUP TEMP FILES
    ; Remove any leftover temp files from installation/operation
    ; =========================================================================
    DetailPrint "[CLEANUP] Removing temporary files..."
    
    ; Remove installer temp scripts
    Delete "$TEMP\sionyx_kiosk_setup.ps1"
    Delete "$TEMP\create_task.ps1"
    
    ; Remove any SIONYX temp folders
    RMDir /r "$TEMP\SIONYX"
    RMDir /r "$TEMP\sionyx"
    RMDir /r "$TEMP\_MEI*"
    
    ; Remove KioskUser temp files
    RMDir /r "C:\Users\${KIOSK_USERNAME}\AppData\Local\Temp\SIONYX"
    RMDir /r "C:\Users\${KIOSK_USERNAME}\AppData\Local\Temp\sionyx"
    
    DetailPrint "[OK] Application data cleaned up"
    DetailPrint ""
    
    ; =========================================================================
    ; ASK ABOUT KIOSK USER REMOVAL
    ; =========================================================================
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove the '${KIOSK_USERNAME}' Windows account?$\n$\n\
        Choose YES to completely remove the kiosk setup.$\n\
        Choose NO to keep the account (you can remove it later)." \
        IDYES removeUser IDNO skipRemoveUser
    
    removeUser:
        DetailPrint "[CLEANUP] Removing KioskUser account..."
        
        ; Remove registry restrictions first
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\" -Name \"NoRun\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableRegistryTools\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableCMD\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableTaskMgr\" -ErrorAction SilentlyContinue"'
        
        ; Remove the user account
        nsExec::ExecToLog 'powershell -Command "Remove-LocalUser -Name \"${KIOSK_USERNAME}\" -ErrorAction SilentlyContinue"'
        
        ; Ask about removing user profile folder
        MessageBox MB_YESNO|MB_ICONEXCLAMATION \
            "Do you also want to delete the KioskUser profile folder?$\n$\n\
            Location: C:\Users\${KIOSK_USERNAME}$\n$\n\
            WARNING: This will delete any files saved by kiosk users!" \
            IDYES removeProfile IDNO skipRemoveProfile
        
        removeProfile:
            DetailPrint "[CLEANUP] Removing KioskUser profile folder..."
            RMDir /r "C:\Users\${KIOSK_USERNAME}"
            DetailPrint "[OK] KioskUser profile removed"
        skipRemoveProfile:
        
        DetailPrint "[OK] KioskUser account removed"
    
    skipRemoveUser:
    
    ; Remove registry entries (all SIONYX config and uninstall info)
    DetailPrint "[CLEANUP] Removing registry entries..."
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "SOFTWARE\${APP_NAME}"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
    
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  SIONYX Uninstallation Complete"
    DetailPrint "============================================"
    DetailPrint ""
SectionEnd

; ============================================================================
; CUSTOM PAGE: Organization Name
; ============================================================================
Function OrgPagePre
    nsDialogs::Create 1018
    Pop $0
    
    ; Title with big font
    ${NSD_CreateLabel} 0 0 100% 24u "Organization Setup"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $BigFont 0
    
    ; Label with medium font
    ${NSD_CreateLabel} 0 30u 100% 18u "Enter your organization or business name:"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $MediumFont 0
    
    ; Larger input field
    ${NSD_CreateText} 0 52u 100% 18u ""
    Pop $OrgNameInput
    SendMessage $OrgNameInput ${WM_SETFONT} $MediumFont 0
    
    ; Description with medium font
    ${NSD_CreateLabel} 0 80u 100% 50u \
        "This identifies your location in the SIONYX system.$\n$\n\
        Examples: 'City Gaming Center', 'Tech Hub Cafe', 'Library Station 1'"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $MediumFont 0
    
    nsDialogs::Show
FunctionEnd

Function OrgPageLeave
    ${NSD_GetText} $OrgNameInput $OrgNameText
    
    StrLen $1 $OrgNameText
    ${If} $1 < 3
        MessageBox MB_OK|MB_ICONEXCLAMATION "Please enter a valid organization name (at least 3 characters)."
        Abort
    ${EndIf}
FunctionEnd

; ============================================================================
; INITIALIZATION
; ============================================================================
Function .onInit
    ; ========================================================================
    ; ADMIN CHECK - Must run as Administrator to create users
    ; ========================================================================
    UserInfo::GetAccountType
    Pop $0
    StrCmp $0 "Admin" +3 0
        MessageBox MB_OK|MB_ICONSTOP "This installer must be run as Administrator.$\n$\nPlease right-click the installer and select$\n'Run as administrator'."
        Abort
    
    ; Create larger fonts for better readability
    CreateFont $BigFont "Segoe UI" 12 700      ; Bold, 12pt for titles
    CreateFont $MediumFont "Segoe UI" 10 400   ; Normal, 10pt for content
    
    ; ========================================================================
    ; UPGRADE CHECK - Detect existing installation
    ; IMPORTANT: Use 64-bit registry view to match where we install!
    ; Without this, we read from WOW6432Node and miss existing installs.
    ; ========================================================================
    SetRegView 64
    
    ; Check if already installed
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
    StrCmp $R0 "" check_32bit
    Goto found_existing
    
    ; Fallback: Also check 32-bit registry (for older installations)
    check_32bit:
    SetRegView 32
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
    SetRegView 64  ; Reset to 64-bit for rest of installer
    StrCmp $R0 "" done
    
    found_existing:
    ; Get the installed version for display
    ReadRegStr $R1 HKLM "SOFTWARE\${APP_NAME}" "Version"
    StrCmp $R1 "" show_upgrade_no_version show_upgrade_with_version
    
    show_upgrade_with_version:
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} version $R1 is already installed.$\n$\n\
        Click 'OK' to upgrade to version ${VERSION}.$\n\
        Click 'Cancel' to abort installation." \
        IDOK uninst
    Abort
    
    show_upgrade_no_version:
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} is already installed.$\n$\n\
        Click 'OK' to remove the previous version and install version ${VERSION}.$\n\
        Click 'Cancel' to abort." \
        IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        ; Run uninstaller silently with _?= to wait for completion
        ExecWait '$R0 _?=$INSTDIR'
        
        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:
    done:
FunctionEnd
