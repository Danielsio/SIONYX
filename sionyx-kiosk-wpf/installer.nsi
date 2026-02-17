; SIONYX WPF Installer Script for NSIS
; Creates a professional Windows installer with integrated kiosk setup
; Adapted from the PyQt6 installer for the WPF/.NET 8 build

!define APP_NAME "SIONYX"
; VERSION is passed from build script via /DVERSION="x.y.z"
!ifndef VERSION
    !define VERSION "0.0.0"
!endif
!define APP_PUBLISHER "SIONYX Technologies"
!define APP_URL "https://sionyx.app"
!define APP_EXECUTABLE "SionyxKiosk.exe"
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
Page custom OrgPagePre OrgPageLeave
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
    SetRegView 64
    SetOutPath "$INSTDIR"
    
    ; Copy main executable (single-file .NET 8 publish output)
    File "${APP_EXECUTABLE}"
    
    ; Copy application icon
    File "${APP_ICON}"
    
    ; Copy Assets (templates, etc.)
    SetOutPath "$INSTDIR\Assets\templates"
    File /nonfatal "Assets\templates\*.*"
    SetOutPath "$INSTDIR"
    
    ; =========================================================================
    ; Store ALL configuration in Windows Registry
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
    
    ; Security
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
    
    ; Create shortcuts
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_ICON}" 0
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_ICON}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
SectionEnd

; ============================================================================
; KIOSK SETUP SECTION
; ============================================================================
Section "Kiosk Security Setup" SecKiosk
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  STEP 1: Creating Kiosk User Account"
    DetailPrint "============================================"
    DetailPrint ""
    
    ; Enable blank password logon
    nsExec::ExecToLog 'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LimitBlankPasswordUse /t REG_DWORD /d 0 /f'
    Pop $0
    
    ; Check if user exists
    nsExec::ExecToLog 'net user "${KIOSK_USERNAME}"'
    Pop $0
    
    ${If} $0 == 0
        DetailPrint "[INFO] User '${KIOSK_USERNAME}' already exists"
        nsExec::ExecToLog 'net user "${KIOSK_USERNAME}" ""'
        Pop $0
    ${Else}
        DetailPrint "[CREATING] New user account '${KIOSK_USERNAME}'..."
        nsExec::ExecToLog 'net user "${KIOSK_USERNAME}" "" /add /fullname:"SIONYX Kiosk User" /comment:"Restricted kiosk account" /passwordchg:no'
        Pop $0
        ${If} $0 != 0
            MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to create KioskUser account (error $0)"
            Abort
        ${EndIf}
        nsExec::ExecToLog 'wmic useraccount where name="${KIOSK_USERNAME}" set PasswordExpires=false'
        Pop $0
    ${EndIf}
    
    ; Ensure not admin
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "Remove-LocalGroupMember -Group ''Administrators'' -Member ''${KIOSK_USERNAME}'' -ErrorAction SilentlyContinue"'
    Pop $0
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "Add-LocalGroupMember -Group ''Users'' -Member ''${KIOSK_USERNAME}'' -ErrorAction SilentlyContinue"'
    Pop $0
    
    DetailPrint "[OK] Kiosk user account ready!"
    DetailPrint ""
    
    ; ========================================================================
    DetailPrint "============================================"
    DetailPrint "  STEP 2: Applying Security Restrictions"
    DetailPrint "============================================"
    DetailPrint ""
    
    ; Apply registry restrictions via PowerShell
    FileOpen $0 "$TEMP\sionyx_kiosk_setup.ps1" w
    FileWrite $0 '$$explorerPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"$\r$\n'
    FileWrite $0 '$$systemPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"$\r$\n'
    FileWrite $0 'if (-not (Test-Path $$explorerPath)) { New-Item -Path $$explorerPath -Force | Out-Null }$\r$\n'
    FileWrite $0 'if (-not (Test-Path $$systemPath)) { New-Item -Path $$systemPath -Force | Out-Null }$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$explorerPath -Name "NoRun" -Value 1 -Type DWord -Force$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableRegistryTools" -Value 1 -Type DWord -Force$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableCMD" -Value 2 -Type DWord -Force$\r$\n'
    FileWrite $0 'Set-ItemProperty -Path $$systemPath -Name "DisableTaskMgr" -Value 1 -Type DWord -Force$\r$\n'
    FileClose $0
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_kiosk_setup.ps1"'
    Pop $0
    Delete "$TEMP\sionyx_kiosk_setup.ps1"
    DetailPrint "[OK] Security restrictions applied!"
    DetailPrint ""
    
    ; ========================================================================
    DetailPrint "============================================"
    DetailPrint "  STEP 3: Setting Up Auto-Start"
    DetailPrint "============================================"
    DetailPrint ""
    
    ; Scheduled task
    nsExec::ExecToLog 'schtasks /delete /tn "SIONYX Kiosk" /f'
    
    FileOpen $1 "$TEMP\create_sionyx_task.ps1" w
    FileWrite $1 '$$action = New-ScheduledTaskAction -Execute "$INSTDIR\${APP_EXECUTABLE}" -Argument "--kiosk"$\r$\n'
    FileWrite $1 '$$trigger = New-ScheduledTaskTrigger -AtLogOn -User "${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 '$$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)$\r$\n'
    FileWrite $1 '$$principal = New-ScheduledTaskPrincipal -UserId "${KIOSK_USERNAME}" -LogonType Interactive -RunLevel Limited$\r$\n'
    FileWrite $1 'Register-ScheduledTask -TaskName "SIONYX Kiosk" -Action $$action -Trigger $$trigger -Settings $$settings -Principal $$principal -Force$\r$\n'
    FileClose $1
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\create_sionyx_task.ps1"'
    Pop $0
    Delete "$TEMP\create_sionyx_task.ps1"
    
    ; Force Windows profile initialization for KioskUser.
    ; Windows only creates a proper user profile on first interactive logon.
    ; Without this, manually creating C:\Users\KioskUser causes a "temporary
    ; profile" error because the registry ProfileList entry is missing.
    ;
    ; We use the Win32 CreateProfile API (userenv.dll) to create the profile
    ; programmatically. This is the official Windows API for this purpose --
    ; no credentials or interactive logon required, just needs admin rights.
    IfFileExists "C:\Users\${KIOSK_USERNAME}\ntuser.dat" profile_ready 0
    
    DetailPrint "[INFO] Initializing Windows profile for ${KIOSK_USERNAME}..."
    
    FileOpen $1 "$TEMP\init_profile.ps1" w
    FileWrite $1 '# Create user profile via Win32 CreateProfile API (userenv.dll)$\r$\n'
    FileWrite $1 '# This creates ProfileList registry entry + ntuser.dat without login$\r$\n'
    FileWrite $1 'try {$\r$\n'
    FileWrite $1 '    Add-Type -TypeDefinition @"$\r$\n'
    FileWrite $1 'using System;$\r$\n'
    FileWrite $1 'using System.Text;$\r$\n'
    FileWrite $1 'using System.Runtime.InteropServices;$\r$\n'
    FileWrite $1 'public class WinProfile {$\r$\n'
    FileWrite $1 '    [DllImport("userenv.dll", CharSet = CharSet.Unicode, SetLastError = true)]$\r$\n'
    FileWrite $1 '    public static extern int CreateProfile($\r$\n'
    FileWrite $1 '        [MarshalAs(UnmanagedType.LPWStr)] string pszUserSid,$\r$\n'
    FileWrite $1 '        [MarshalAs(UnmanagedType.LPWStr)] string pszUserName,$\r$\n'
    FileWrite $1 '        [Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszProfilePath,$\r$\n'
    FileWrite $1 '        uint cchProfilePath);$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '"@$\r$\n'
    FileWrite $1 '    $$acct = New-Object System.Security.Principal.NTAccount("${KIOSK_USERNAME}")$\r$\n'
    FileWrite $1 '    $$sid = $$acct.Translate([System.Security.Principal.SecurityIdentifier]).Value$\r$\n'
    FileWrite $1 '    Write-Host "[INFO] SID for ${KIOSK_USERNAME}: $$sid"$\r$\n'
    FileWrite $1 '    $$pathBuf = New-Object System.Text.StringBuilder(260)$\r$\n'
    FileWrite $1 '    $$hr = [WinProfile]::CreateProfile($$sid, "${KIOSK_USERNAME}", $$pathBuf, 260)$\r$\n'
    FileWrite $1 '    if ($$hr -eq 0) {$\r$\n'
    FileWrite $1 '        Write-Host "[OK] Profile created at: $$($$pathBuf.ToString())"$\r$\n'
    FileWrite $1 '    } else {$\r$\n'
    FileWrite $1 '        Write-Host "[WARN] CreateProfile HRESULT: 0x$$($$hr.ToString(''X8''))"$\r$\n'
    FileWrite $1 '        Write-Host "[INFO] Profile may already exist or will be created on first logon"$\r$\n'
    FileWrite $1 '    }$\r$\n'
    FileWrite $1 '} catch {$\r$\n'
    FileWrite $1 '    Write-Host "[WARN] Profile init failed: $$_"$\r$\n'
    FileWrite $1 '    Write-Host "[INFO] Profile will be created on first logon"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileClose $1
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\init_profile.ps1"'
    Pop $0
    Delete "$TEMP\init_profile.ps1"
    
    profile_ready:
    
    ; Now create app-specific directories inside the (properly initialized) profile
    FileOpen $1 "$TEMP\create_profile_dirs.ps1" w
    FileWrite $1 '$$profilePath = "C:\Users\${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 '$$startupPath = "$$profilePath\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"$\r$\n'
    FileWrite $1 'New-Item -Path $$startupPath -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $1 'New-Item -Path "$$profilePath\.sionyx" -ItemType Directory -Force | Out-Null$\r$\n'
    FileWrite $1 'New-Item -Path "$$profilePath\AppData\Local\SIONYX\logs" -ItemType Directory -Force | Out-Null$\r$\n'
    FileClose $1
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\create_profile_dirs.ps1"'
    Pop $0
    Delete "$TEMP\create_profile_dirs.ps1"
    
    ; Create startup shortcut
    CreateShortCut "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXECUTABLE}" "--kiosk" "$INSTDIR\${APP_ICON}" 0
    
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "KioskUsername" "${KIOSK_USERNAME}"
    
    DetailPrint ""
    DetailPrint "  SETUP COMPLETE!"
    DetailPrint ""
SectionEnd

; ============================================================================
; UNINSTALLER SECTION
; ============================================================================
Section "Uninstall"
    SetRegView 64
    
    Delete "$INSTDIR\${APP_EXECUTABLE}"
    Delete "$INSTDIR\${APP_ICON}"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\Assets"
    
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    nsExec::ExecToLog 'schtasks /delete /tn "SIONYX Kiosk" /f'
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
    Delete "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    
    ; Cleanup app data
    RMDir /r "$PROFILE\.sionyx"
    RMDir /r "$LOCALAPPDATA\${APP_NAME}"
    RMDir /r "C:\Users\${KIOSK_USERNAME}\.sionyx"
    RMDir /r "C:\Users\${KIOSK_USERNAME}\AppData\Local\${APP_NAME}"
    
    ; Ask about KioskUser removal
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Remove '${KIOSK_USERNAME}' Windows account?" \
        IDYES removeUser IDNO skipRemoveUser
    
    removeUser:
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\" -Name \"NoRun\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableRegistryTools\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableCMD\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-ItemProperty -Path \"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\" -Name \"DisableTaskMgr\" -ErrorAction SilentlyContinue"'
        nsExec::ExecToLog 'powershell -Command "Remove-LocalUser -Name \"${KIOSK_USERNAME}\" -ErrorAction SilentlyContinue"'
    
    skipRemoveUser:
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "SOFTWARE\${APP_NAME}"
    RMDir "$INSTDIR"
SectionEnd

; ============================================================================
; CUSTOM PAGE: Organization Name
; ============================================================================
Function OrgPagePre
    nsDialogs::Create 1018
    Pop $0
    ${NSD_CreateLabel} 0 0 100% 24u "Organization Setup"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $BigFont 0
    ${NSD_CreateLabel} 0 30u 100% 18u "Enter your organization or business name:"
    Pop $0
    SendMessage $0 ${WM_SETFONT} $MediumFont 0
    ${NSD_CreateText} 0 52u 100% 18u ""
    Pop $OrgNameInput
    SendMessage $OrgNameInput ${WM_SETFONT} $MediumFont 0
    ${NSD_CreateLabel} 0 80u 100% 50u \
        "This identifies your location in the SIONYX system.$\n$\nExamples: 'City Gaming Center', 'Tech Hub Cafe'"
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
    UserInfo::GetAccountType
    Pop $0
    StrCmp $0 "Admin" +3 0
        MessageBox MB_OK|MB_ICONSTOP "This installer must be run as Administrator."
        Abort
    
    CreateFont $BigFont "Segoe UI" 12 700
    CreateFont $MediumFont "Segoe UI" 10 400
    
    SetRegView 64
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
    StrCmp $R0 "" done
    
    ReadRegStr $R1 HKLM "SOFTWARE\${APP_NAME}" "Version"
    StrCmp $R1 "" show_upgrade_no_version show_upgrade_with_version
    
    show_upgrade_with_version:
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} v$R1 is installed. Click OK to upgrade to v${VERSION}." \
        IDOK uninst
    Abort
    
    show_upgrade_no_version:
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} is already installed. Click OK to upgrade to v${VERSION}." \
        IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        ExecWait '$R0 _?=$INSTDIR'
        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:
    done:
FunctionEnd
