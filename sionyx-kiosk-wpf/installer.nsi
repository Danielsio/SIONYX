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
!define KIOSK_USERNAME "SionyxUser"

; Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"

; ListView messages for DumpLog
!ifndef LVM_GETITEMCOUNT
    !define LVM_GETITEMCOUNT 0x1004
!endif
!ifndef LVM_GETITEMTEXT
    !define LVM_GETITEMTEXT 0x102D
!endif

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

; Always show the install/uninstall log so the admin can see what's happening
ShowInstDetails show
ShowUnInstDetails show

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
            MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to create SionyxUser account (error $0)"
            Abort
        ${EndIf}
        nsExec::ExecToLog 'wmic useraccount where name="${KIOSK_USERNAME}" set PasswordExpires=false'
        Pop $0
    ${EndIf}
    
    ; Ensure not admin (use net localgroup - always available unlike *-LocalGroupMember cmdlets)
    nsExec::ExecToLog 'net localgroup Administrators "${KIOSK_USERNAME}" /delete'
    Pop $0
    nsExec::ExecToLog 'net localgroup Users "${KIOSK_USERNAME}" /add'
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
    ${If} $0 != 0
        DetailPrint "[WARN] Security policy script returned error code $0"
    ${Else}
        DetailPrint "[OK] Security restrictions applied!"
    ${EndIf}
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
    ${If} $0 != 0
        DetailPrint "[WARN] Scheduled task creation script returned error code $0"
    ${Else}
        DetailPrint "[OK] Scheduled task created!"
    ${EndIf}
    
    ; Force Windows profile initialization for SionyxUser.
    ; Windows only creates a proper user profile on first interactive logon.
    ; Without this, manually creating C:\Users\SionyxUser causes a "temporary
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
    FileWrite $1 '        Write-Host "[WARN] CreateProfile HRESULT: $$hr"$\r$\n'
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
    ${If} $0 != 0
        DetailPrint "[WARN] Profile initialization script returned error code $0"
    ${Else}
        DetailPrint "[OK] Profile initialized!"
    ${EndIf}
    
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
    ${If} $0 != 0
        DetailPrint "[WARN] Profile directory creation script returned error code $0"
    ${Else}
        DetailPrint "[OK] Profile directories created!"
    ${EndIf}
    
    ; Create startup shortcut
    CreateShortCut "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXECUTABLE}" "--kiosk" "$INSTDIR\${APP_ICON}" 0
    
    WriteRegStr HKLM "SOFTWARE\${APP_NAME}" "KioskUsername" "${KIOSK_USERNAME}"
    
    DetailPrint ""
    DetailPrint "============================================"
    DetailPrint "  STEP 4: Post-Install Verification"
    DetailPrint "============================================"
    DetailPrint ""
    
    ; Save install log to disk BEFORE verification so the verify script can append to it
    StrCpy $0 "$INSTDIR\install.log"
    Push $0
    Call DumpLog
    
    ; Run comprehensive post-install verification
    FileOpen $1 "$TEMP\sionyx_verify_install.ps1" w
    FileWrite $1 '$$logFile = "$INSTDIR\install.log"$\r$\n'
    FileWrite $1 '$$errors = @()$\r$\n'
    FileWrite $1 '$$warnings = @()$\r$\n'
    FileWrite $1 '$$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 'function Log($$msg) { Write-Host $$msg; Add-Content -Path $$logFile -Value $$msg }$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 'Log ""$\r$\n'
    FileWrite $1 'Log "============================================"$\r$\n'
    FileWrite $1 'Log "  POST-INSTALL VERIFICATION ($$timestamp)"$\r$\n'
    FileWrite $1 'Log "============================================"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 1. Check SionyxUser account exists$\r$\n'
    FileWrite $1 'net user "${KIOSK_USERNAME}" 2>&1 | Out-Null$\r$\n'
    FileWrite $1 'if ($$LASTEXITCODE -eq 0) {$\r$\n'
    FileWrite $1 '    Log "[PASS] User account ${KIOSK_USERNAME} exists"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[FAIL] User account ${KIOSK_USERNAME} NOT FOUND"$\r$\n'
    FileWrite $1 '    $$errors += "User account ${KIOSK_USERNAME} was not created"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 2. Check user profile directory & registry$\r$\n'
    FileWrite $1 '$$profilePath = "C:\Users\${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 'if (Test-Path $$profilePath) {$\r$\n'
    FileWrite $1 '    Log "[PASS] Profile directory exists: $$profilePath"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[FAIL] Profile directory MISSING: $$profilePath"$\r$\n'
    FileWrite $1 '    $$errors += "User profile directory was not created"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Check ProfileList registry entry$\r$\n'
    FileWrite $1 'try {$\r$\n'
    FileWrite $1 '    $$acct = New-Object System.Security.Principal.NTAccount("${KIOSK_USERNAME}")$\r$\n'
    FileWrite $1 '    $$sid = $$acct.Translate([System.Security.Principal.SecurityIdentifier]).Value$\r$\n'
    FileWrite $1 '    $$regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$$sid"$\r$\n'
    FileWrite $1 '    if (Test-Path $$regPath) {$\r$\n'
    FileWrite $1 '        Log "[PASS] Profile registry entry exists (SID: $$sid)"$\r$\n'
    FileWrite $1 '    } else {$\r$\n'
    FileWrite $1 '        Log "[FAIL] Profile registry entry MISSING for SID $$sid"$\r$\n'
    FileWrite $1 '        $$errors += "ProfileList registry entry not found - user may get a temporary profile on login"$\r$\n'
    FileWrite $1 '    }$\r$\n'
    FileWrite $1 '} catch {$\r$\n'
    FileWrite $1 '    Log "[FAIL] Could not resolve SID for ${KIOSK_USERNAME}: $$_"$\r$\n'
    FileWrite $1 '    $$errors += "Could not verify profile registry (SID resolution failed)"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 3. Check ntuser.dat (profile properly initialized)$\r$\n'
    FileWrite $1 'if (Test-Path "$$profilePath\ntuser.dat" -ErrorAction SilentlyContinue) {$\r$\n'
    FileWrite $1 '    Log "[PASS] Profile initialized (ntuser.dat present)"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[WARN] Cannot verify ntuser.dat (access denied or missing)"$\r$\n'
    FileWrite $1 '    $$warnings += "ntuser.dat could not be verified - profile may need first logon to initialize"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 4. Check scheduled task$\r$\n'
    FileWrite $1 '$$task = $null$\r$\n'
    FileWrite $1 'try { $$task = Get-ScheduledTask -TaskName "SIONYX Kiosk" -ErrorAction Stop } catch {}$\r$\n'
    FileWrite $1 'if ($$task) {$\r$\n'
    FileWrite $1 '    Log "[PASS] Scheduled task SIONYX Kiosk exists (State: $$($$task.State))"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[FAIL] Scheduled task SIONYX Kiosk NOT FOUND"$\r$\n'
    FileWrite $1 '    $$errors += "Scheduled task was not created - app will not auto-start on ${KIOSK_USERNAME} login"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 5. Check app executable$\r$\n'
    FileWrite $1 'if (Test-Path "$INSTDIR\${APP_EXECUTABLE}") {$\r$\n'
    FileWrite $1 '    Log "[PASS] App executable: $INSTDIR\${APP_EXECUTABLE}"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[FAIL] App executable MISSING: $INSTDIR\${APP_EXECUTABLE}"$\r$\n'
    FileWrite $1 '    $$errors += "Application executable was not installed"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 6. Check startup shortcut$\r$\n'
    FileWrite $1 '$$startupLnk = "$$profilePath\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"$\r$\n'
    FileWrite $1 'if (Test-Path $$startupLnk) {$\r$\n'
    FileWrite $1 '    Log "[PASS] Startup shortcut exists for ${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[WARN] Startup shortcut not found at expected path"$\r$\n'
    FileWrite $1 '    $$warnings += "Startup shortcut missing - app may not auto-start via Startup folder"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# 7. Check registry configuration$\r$\n'
    FileWrite $1 '$$regKeys = @("Install_Dir", "Version", "OrgId", "FirebaseProjectId", "KioskUsername")$\r$\n'
    FileWrite $1 '$$missingKeys = @()$\r$\n'
    FileWrite $1 'foreach ($$key in $$regKeys) {$\r$\n'
    FileWrite $1 '    $$val = Get-ItemProperty -Path "HKLM:\SOFTWARE\${APP_NAME}" -Name $$key -ErrorAction SilentlyContinue$\r$\n'
    FileWrite $1 '    if (-not $$val) { $$missingKeys += $$key }$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 'if ($$missingKeys.Count -eq 0) {$\r$\n'
    FileWrite $1 '    Log "[PASS] All registry configuration keys present"$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[FAIL] Missing registry keys: $$($$missingKeys -join ", ")"$\r$\n'
    FileWrite $1 '    $$errors += "Registry configuration incomplete - missing: $$($$missingKeys -join ", ")"$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# === FINAL SUMMARY ===$\r$\n'
    FileWrite $1 'Log ""$\r$\n'
    FileWrite $1 'Log "--------------------------------------------"$\r$\n'
    FileWrite $1 'if ($$errors.Count -eq 0 -and $$warnings.Count -eq 0) {$\r$\n'
    FileWrite $1 '    Log "[OK] ALL CHECKS PASSED - Installation verified successfully!"$\r$\n'
    FileWrite $1 '} elseif ($$errors.Count -eq 0) {$\r$\n'
    FileWrite $1 '    Log "[OK] Installation completed with $$( $$warnings.Count) warning(s):"$\r$\n'
    FileWrite $1 '    foreach ($$w in $$warnings) { Log "  - $$w" }$\r$\n'
    FileWrite $1 '} else {$\r$\n'
    FileWrite $1 '    Log "[ERROR] Installation completed with $$($$errors.Count) error(s) and $$($$warnings.Count) warning(s):"$\r$\n'
    FileWrite $1 '    Log ""$\r$\n'
    FileWrite $1 '    Log "  ERRORS:"$\r$\n'
    FileWrite $1 '    foreach ($$e in $$errors) { Log "    - $$e" }$\r$\n'
    FileWrite $1 '    if ($$warnings.Count -gt 0) {$\r$\n'
    FileWrite $1 '        Log "  WARNINGS:"$\r$\n'
    FileWrite $1 '        foreach ($$w in $$warnings) { Log "    - $$w" }$\r$\n'
    FileWrite $1 '    }$\r$\n'
    FileWrite $1 '}$\r$\n'
    FileWrite $1 'Log ""$\r$\n'
    FileWrite $1 'Log "  Install log: $$logFile"$\r$\n'
    FileWrite $1 'Log "  To debug, review the log above for [FAIL] or [WARN] entries."$\r$\n'
    FileWrite $1 'Log "  You can also run Task Scheduler (taskschd.msc) and check the SIONYX Kiosk task."$\r$\n'
    FileWrite $1 'Log "  For user profile issues, check: lusrmgr.msc or run: net user ${KIOSK_USERNAME}"$\r$\n'
    FileWrite $1 'Log "--------------------------------------------"$\r$\n'
    FileWrite $1 '$\r$\n'
    FileWrite $1 '# Return error count as exit code so NSIS can detect failures$\r$\n'
    FileWrite $1 'exit $$errors.Count$\r$\n'
    FileClose $1
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_verify_install.ps1"'
    Pop $0
    Delete "$TEMP\sionyx_verify_install.ps1"
    
    ${If} $0 != 0
        DetailPrint ""
        DetailPrint "[WARNING] Some verification checks failed!"
        DetailPrint "Review the install log for details: $INSTDIR\install.log"
        DetailPrint ""
        MessageBox MB_OK|MB_ICONEXCLAMATION \
            "Installation completed but $0 verification check(s) failed.$\n$\n\
            Please review the install log for details:$\n\
            $INSTDIR\install.log$\n$\n\
            Look for [FAIL] entries in the log.$\n\
            Common debug tools:$\n\
            - Task Scheduler: taskschd.msc$\n\
            - User accounts: net user ${KIOSK_USERNAME}$\n\
            - Profile issues: lusrmgr.msc"
    ${Else}
        DetailPrint ""
        DetailPrint "[OK] All verification checks passed!"
        DetailPrint ""
    ${EndIf}
    
    DetailPrint ""
    DetailPrint "  SETUP COMPLETE!"
    DetailPrint ""
    DetailPrint "[OK] Install log saved to $INSTDIR\install.log"
SectionEnd

; ============================================================================
; UNINSTALLER SECTION
; ============================================================================
Section "Uninstall"
    SetRegView 64
    
    DetailPrint ""
    DetailPrint "============================================================"
    DetailPrint "  SIONYX Uninstaller"
    DetailPrint "============================================================"
    DetailPrint ""
    
    ; ── STEP 1: Kill running processes ────────────────────────────
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 1: Stopping running processes"
    DetailPrint "------------------------------------------------------------"
    
    nsExec::ExecToLog 'taskkill /F /IM SionyxKiosk.exe'
    Pop $0
    ${If} $0 == 0
        DetailPrint "[OK] SionyxKiosk process terminated"
    ${Else}
        DetailPrint "[INFO] SionyxKiosk was not running"
    ${EndIf}
    
    ; ── STEP 2: Remove scheduled task ─────────────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 2: Removing scheduled task"
    DetailPrint "------------------------------------------------------------"
    
    nsExec::ExecToLog 'schtasks /delete /tn "SIONYX Kiosk" /f'
    Pop $0
    ${If} $0 == 0
        DetailPrint "[OK] Scheduled task removed"
    ${Else}
        DetailPrint "[INFO] Scheduled task not found (already removed)"
    ${EndIf}
    
    DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
    DetailPrint "[OK] Auto-run registry entry cleared"
    
    ; ── STEP 3: Remove application files ──────────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 3: Removing application files"
    DetailPrint "------------------------------------------------------------"
    
    Delete "$INSTDIR\${APP_EXECUTABLE}"
    DetailPrint "  Deleted: $INSTDIR\${APP_EXECUTABLE}"
    Delete "$INSTDIR\${APP_ICON}"
    DetailPrint "  Deleted: $INSTDIR\${APP_ICON}"
    Delete "$INSTDIR\install.log"
    DetailPrint "  Deleted: $INSTDIR\install.log"
    RMDir /r "$INSTDIR\Assets"
    DetailPrint "  Deleted: $INSTDIR\Assets\"
    
    ; Shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    DetailPrint "  Deleted: Desktop shortcut"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    DetailPrint "  Deleted: Start Menu shortcuts"
    Delete "C:\Users\${KIOSK_USERNAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    DetailPrint "  Deleted: SionyxUser startup shortcut"
    ; Legacy KioskUser startup shortcut
    Delete "C:\Users\KioskUser\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    Delete "C:\Users\KioskUser.000\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\${APP_NAME}.lnk"
    
    DetailPrint "[OK] Application files removed"
    
    ; ── STEP 4: Remove app data ───────────────────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 4: Removing application data"
    DetailPrint "------------------------------------------------------------"
    
    ; Current user's app data
    RMDir /r "$PROFILE\.sionyx"
    DetailPrint "  Cleaned: $PROFILE\.sionyx"
    RMDir /r "$LOCALAPPDATA\${APP_NAME}"
    DetailPrint "  Cleaned: $LOCALAPPDATA\${APP_NAME}"
    
    ; SionyxUser app data
    RMDir /r "C:\Users\${KIOSK_USERNAME}\.sionyx"
    DetailPrint "  Cleaned: C:\Users\${KIOSK_USERNAME}\.sionyx"
    RMDir /r "C:\Users\${KIOSK_USERNAME}\AppData\Local\${APP_NAME}"
    DetailPrint "  Cleaned: C:\Users\${KIOSK_USERNAME}\AppData\Local\${APP_NAME}"
    
    ; Legacy KioskUser app data (pre-v3.0.16)
    RMDir /r "C:\Users\KioskUser\.sionyx"
    RMDir /r "C:\Users\KioskUser\AppData\Local\${APP_NAME}"
    RMDir /r "C:\Users\KioskUser.000\.sionyx"
    RMDir /r "C:\Users\KioskUser.000\AppData\Local\${APP_NAME}"
    
    DetailPrint "[OK] Application data removed"
    
    ; ── STEP 5: Revert security restrictions ──────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 5: Reverting security restrictions"
    DetailPrint "------------------------------------------------------------"
    
    FileOpen $0 "$TEMP\sionyx_revert_security.ps1" w
    FileWrite $0 '$$removedCount = 0$\r$\n'
    FileWrite $0 '$$policies = @($\r$\n'
    FileWrite $0 '    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"; Name = "NoRun" },$\r$\n'
    FileWrite $0 '    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "DisableRegistryTools" },$\r$\n'
    FileWrite $0 '    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "DisableCMD" },$\r$\n'
    FileWrite $0 '    @{ Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"; Name = "DisableTaskMgr" }$\r$\n'
    FileWrite $0 ')$\r$\n'
    FileWrite $0 'foreach ($$p in $$policies) {$\r$\n'
    FileWrite $0 '    try {$\r$\n'
    FileWrite $0 '        $$val = Get-ItemProperty -Path $$p.Path -Name $$p.Name -ErrorAction Stop$\r$\n'
    FileWrite $0 '        Remove-ItemProperty -Path $$p.Path -Name $$p.Name -Force$\r$\n'
    FileWrite $0 '        Write-Host "[OK] Removed policy: $$($$p.Name)"$\r$\n'
    FileWrite $0 '        $$removedCount++$\r$\n'
    FileWrite $0 '    } catch {$\r$\n'
    FileWrite $0 '        Write-Host "[INFO] Policy not set: $$($$p.Name)"$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 'Write-Host "[OK] Reverted $$removedCount security policies"$\r$\n'
    FileClose $0
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_revert_security.ps1"'
    Pop $0
    Delete "$TEMP\sionyx_revert_security.ps1"
    
    ; ── STEP 6: Remove SionyxUser completely ───────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 6: Removing SionyxUser account & profile"
    DetailPrint "------------------------------------------------------------"
    
    FileOpen $0 "$TEMP\sionyx_remove_user.ps1" w
    FileWrite $0 '$$username = "${KIOSK_USERNAME}"$\r$\n'
    FileWrite $0 '$$profilePath = "C:\Users\$$username"$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Check if user exists using net user (always available, unlike Get-LocalUser)$\r$\n'
    FileWrite $0 '$$netOut = net user $$username 2>&1$\r$\n'
    FileWrite $0 '$$userExists = ($$LASTEXITCODE -eq 0)$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 'if (-not $$userExists) {$\r$\n'
    FileWrite $0 '    Write-Host "[INFO] User $$username does not exist - nothing to remove"$\r$\n'
    FileWrite $0 '} else {$\r$\n'
    FileWrite $0 '    Write-Host "[INFO] Found user: $$username"$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '    # 1. Get user SID before deletion (needed for registry cleanup)$\r$\n'
    FileWrite $0 '    $$sid = $$null$\r$\n'
    FileWrite $0 '    try {$\r$\n'
    FileWrite $0 '        $$acct = New-Object System.Security.Principal.NTAccount($$username)$\r$\n'
    FileWrite $0 '        $$sid = $$acct.Translate([System.Security.Principal.SecurityIdentifier]).Value$\r$\n'
    FileWrite $0 '        Write-Host "[INFO] User SID: $$sid"$\r$\n'
    FileWrite $0 '    } catch {$\r$\n'
    FileWrite $0 '        Write-Host "[WARN] Could not resolve SID: $$_"$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '    # 2. Remove the Windows user account via net user (always available)$\r$\n'
    FileWrite $0 '    net user $$username /delete 2>&1 | Out-Null$\r$\n'
    FileWrite $0 '    if ($$LASTEXITCODE -eq 0) {$\r$\n'
    FileWrite $0 '        Write-Host "[OK] User account removed"$\r$\n'
    FileWrite $0 '    } else {$\r$\n'
    FileWrite $0 '        Write-Host "[ERROR] Failed to remove user account (exit code $$LASTEXITCODE)"$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '    # 3. Remove the user profile via WMI (handles registry + profile path)$\r$\n'
    FileWrite $0 '    if ($$sid) {$\r$\n'
    FileWrite $0 '        try {$\r$\n'
    FileWrite $0 '            $$profile = Get-CimInstance Win32_UserProfile | Where-Object { $$_.SID -eq $$sid }$\r$\n'
    FileWrite $0 '            if ($$profile) {$\r$\n'
    FileWrite $0 '                Remove-CimInstance -InputObject $$profile -ErrorAction Stop$\r$\n'
    FileWrite $0 '                Write-Host "[OK] User profile removed via WMI (SID: $$sid)"$\r$\n'
    FileWrite $0 '            } else {$\r$\n'
    FileWrite $0 '                Write-Host "[INFO] No WMI profile entry found for SID $$sid"$\r$\n'
    FileWrite $0 '            }$\r$\n'
    FileWrite $0 '        } catch {$\r$\n'
    FileWrite $0 '            Write-Host "[WARN] WMI profile removal failed: $$_"$\r$\n'
    FileWrite $0 '        }$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '    # 4. Clean up ProfileList registry entry (in case WMI missed it)$\r$\n'
    FileWrite $0 '    if ($$sid) {$\r$\n'
    FileWrite $0 '        $$regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$$sid"$\r$\n'
    FileWrite $0 '        if (Test-Path $$regPath) {$\r$\n'
    FileWrite $0 '            Remove-Item -Path $$regPath -Recurse -Force$\r$\n'
    FileWrite $0 '            Write-Host "[OK] ProfileList registry entry removed"$\r$\n'
    FileWrite $0 '        } else {$\r$\n'
    FileWrite $0 '            Write-Host "[OK] ProfileList registry entry already clean"$\r$\n'
    FileWrite $0 '        }$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Clean up profile folder regardless of whether user account existed$\r$\n'
    FileWrite $0 'if (Test-Path $$profilePath) {$\r$\n'
    FileWrite $0 '    try {$\r$\n'
    FileWrite $0 '        $$acl = Get-Acl $$profilePath$\r$\n'
    FileWrite $0 '        $$adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")$\r$\n'
    FileWrite $0 '        $$acl.SetAccessRule($$adminRule)$\r$\n'
    FileWrite $0 '        Set-Acl -Path $$profilePath -AclObject $$acl -ErrorAction SilentlyContinue$\r$\n'
    FileWrite $0 '        Remove-Item -Path $$profilePath -Recurse -Force -ErrorAction Stop$\r$\n'
    FileWrite $0 '        Write-Host "[OK] Profile folder deleted: $$profilePath"$\r$\n'
    FileWrite $0 '    } catch {$\r$\n'
    FileWrite $0 '        Write-Host "[WARN] Could not fully delete $$profilePath : $$_"$\r$\n'
    FileWrite $0 '        Write-Host "[INFO] Some files may be locked. They will be removed on next reboot."$\r$\n'
    FileWrite $0 '        cmd /c "rmdir /s /q $$profilePath" 2>$$null$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '} else {$\r$\n'
    FileWrite $0 '    Write-Host "[OK] Profile folder already removed"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Clean up any orphaned ProfileList registry entries for this username$\r$\n'
    FileWrite $0 '$$orphaned = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" -ErrorAction SilentlyContinue | Where-Object { (Get-ItemProperty $$_.PSPath -ErrorAction SilentlyContinue).ProfileImagePath -like "*$$username*" }$\r$\n'
    FileWrite $0 'foreach ($$entry in $$orphaned) {$\r$\n'
    FileWrite $0 '    Remove-Item -Path $$entry.PSPath -Recurse -Force$\r$\n'
    FileWrite $0 '    Write-Host "[OK] Removed orphaned ProfileList entry: $$($$entry.PSChildName)"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '$\r$\n'
    FileWrite $0 '# Final verification using net user (always available)$\r$\n'
    FileWrite $0 'Write-Host ""$\r$\n'
    FileWrite $0 'Write-Host "--- Verification ---"$\r$\n'
    FileWrite $0 'net user $$username 2>&1 | Out-Null$\r$\n'
    FileWrite $0 'if ($$LASTEXITCODE -eq 0) {$\r$\n'
    FileWrite $0 '    Write-Host "[ERROR] User account still exists!"$\r$\n'
    FileWrite $0 '} else {$\r$\n'
    FileWrite $0 '    Write-Host "[OK] User account: REMOVED"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 'if (Test-Path "C:\Users\$$username") {$\r$\n'
    FileWrite $0 '    $$size = (Get-ChildItem "C:\Users\$$username" -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum$\r$\n'
    FileWrite $0 '    $$sizeMB = [math]::Round($$size / 1MB, 1)$\r$\n'
    FileWrite $0 '    Write-Host "[WARN] Profile folder still exists ($${sizeMB} MB) - may need reboot to fully remove"$\r$\n'
    FileWrite $0 '} else {$\r$\n'
    FileWrite $0 '    Write-Host "[OK] Profile folder: REMOVED"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '$$orphanCheck = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" -ErrorAction SilentlyContinue | Where-Object { (Get-ItemProperty $$_.PSPath -ErrorAction SilentlyContinue).ProfileImagePath -like "*$$username*" }$\r$\n'
    FileWrite $0 'if ($$orphanCheck) {$\r$\n'
    FileWrite $0 '    Write-Host "[WARN] Orphaned ProfileList entries still exist"$\r$\n'
    FileWrite $0 '} else {$\r$\n'
    FileWrite $0 '    Write-Host "[OK] ProfileList registry: CLEAN"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileClose $0
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_remove_user.ps1"'
    Pop $0
    Delete "$TEMP\sionyx_remove_user.ps1"
    
    ; ── STEP 6b: Clean up legacy "KioskUser" from older installations ───
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 6b: Cleaning up legacy KioskUser (pre-v3.0.16)"
    DetailPrint "------------------------------------------------------------"
    
    nsExec::ExecToLog 'net user KioskUser 2>&1'
    Pop $0
    ${If} $0 == 0
        nsExec::ExecToLog 'net user KioskUser /delete'
        Pop $0
        DetailPrint "[OK] Legacy KioskUser account removed"
    ${Else}
        DetailPrint "[INFO] No legacy KioskUser account found"
    ${EndIf}
    
    ; Remove legacy profile folders (KioskUser, KioskUser.000, KioskUser.001)
    FileOpen $0 "$TEMP\sionyx_legacy_cleanup.ps1" w
    FileWrite $0 'foreach ($$dir in @("C:\Users\KioskUser", "C:\Users\KioskUser.000", "C:\Users\KioskUser.001")) {$\r$\n'
    FileWrite $0 '    if (Test-Path $$dir) {$\r$\n'
    FileWrite $0 '        try {$\r$\n'
    FileWrite $0 '            $$acl = Get-Acl $$dir$\r$\n'
    FileWrite $0 '            $$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")$\r$\n'
    FileWrite $0 '            $$acl.SetAccessRule($$rule)$\r$\n'
    FileWrite $0 '            Set-Acl -Path $$dir -AclObject $$acl -ErrorAction SilentlyContinue$\r$\n'
    FileWrite $0 '            Remove-Item -Path $$dir -Recurse -Force -ErrorAction Stop$\r$\n'
    FileWrite $0 '            Write-Host "[OK] Deleted legacy folder: $$dir"$\r$\n'
    FileWrite $0 '        } catch {$\r$\n'
    FileWrite $0 '            Write-Host "[WARN] Could not delete $$dir - may need reboot"$\r$\n'
    FileWrite $0 '        }$\r$\n'
    FileWrite $0 '    }$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileWrite $0 '# Clean orphaned ProfileList entries for KioskUser$\r$\n'
    FileWrite $0 '$$orphaned = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList" -ErrorAction SilentlyContinue | Where-Object { (Get-ItemProperty $$_.PSPath -ErrorAction SilentlyContinue).ProfileImagePath -like "*KioskUser*" }$\r$\n'
    FileWrite $0 'foreach ($$e in $$orphaned) {$\r$\n'
    FileWrite $0 '    Remove-Item -Path $$e.PSPath -Recurse -Force$\r$\n'
    FileWrite $0 '    Write-Host "[OK] Removed legacy ProfileList entry: $$($$e.PSChildName)"$\r$\n'
    FileWrite $0 '}$\r$\n'
    FileClose $0
    
    nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -File "$TEMP\sionyx_legacy_cleanup.ps1"'
    Pop $0
    Delete "$TEMP\sionyx_legacy_cleanup.ps1"
    
    ; ── STEP 7: Remove registry entries ───────────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 7: Removing registry entries"
    DetailPrint "------------------------------------------------------------"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DetailPrint "[OK] Add/Remove Programs entry removed"
    DeleteRegKey HKLM "SOFTWARE\${APP_NAME}"
    DetailPrint "[OK] SIONYX registry configuration removed"
    
    ; ── STEP 8: Remove install directory ──────────────────────────
    DetailPrint ""
    DetailPrint "------------------------------------------------------------"
    DetailPrint "  STEP 8: Final cleanup"
    DetailPrint "------------------------------------------------------------"
    
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
    
    IfFileExists "$INSTDIR\*.*" 0 instdir_clean
        DetailPrint "[WARN] Install directory not fully empty: $INSTDIR"
        DetailPrint "[INFO] You may need to manually delete it after reboot"
        Goto instdir_done
    instdir_clean:
        DetailPrint "[OK] Install directory removed: $INSTDIR"
    instdir_done:
    
    DetailPrint ""
    DetailPrint "============================================================"
    DetailPrint "  UNINSTALL COMPLETE"
    DetailPrint "============================================================"
    DetailPrint ""
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
; HELPER: Dump install log to file
; Reads the Details listview and writes all lines to the file path on the stack.
; ============================================================================
Function DumpLog
    Exch $5
    Push $0
    Push $1
    Push $2
    Push $3
    Push $4
    Push $6
    FindWindow $0 "#32770" "" $HWNDPARENT
    GetDlgItem $0 $0 1016
    StrCmp $0 0 exit
    FileOpen $5 $5 w
    StrCmp $5 "" exit
        SendMessage $0 ${LVM_GETITEMCOUNT} 0 0 $6
        System::Alloc ${NSIS_MAX_STRLEN}
        Pop $3
        StrCpy $2 0
        System::Call "*(i, i, i, i, i, p, i, i, i) p (0, 0, 0, 0, 0, r3, ${NSIS_MAX_STRLEN}) .r1"
        loop: StrCmp $2 $6 done
            System::Call "User32::SendMessage(p, i, i, p) p ($0, ${LVM_GETITEMTEXT}, $2, r1)"
            System::Call "*$3(&t${NSIS_MAX_STRLEN} .r4)"
            FileWrite $5 "$4$\r$\n"
            IntOp $2 $2 + 1
            Goto loop
        done:
            FileClose $5
            System::Free $1
            System::Free $3
    exit:
    Pop $6
    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Pop $0
    Exch $5
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
