# ============================================================================
# SIONYX Kiosk Mode Setup Script
# Run this AS ADMINISTRATOR on each PC to set up user restrictions
# ============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  SIONYX Kiosk Mode Security Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 1: Create Kiosk User Account
# ============================================================================
Write-Host "STEP 1: Creating Kiosk User Account..." -ForegroundColor Yellow

$username = "KioskUser"
$password = "Sionyx2024!"  # Change this in production!

$existingUser = Get-LocalUser -Name $username -ErrorAction SilentlyContinue

if ($existingUser) {
    Write-Host "  User '$username' already exists, skipping creation" -ForegroundColor Cyan
} else {
    try {
        $securePassword = ConvertTo-SecureString $password -AsPlainText -Force
        New-LocalUser -Name $username -Password $securePassword -FullName "SIONYX Kiosk User" -Description "Restricted kiosk account for SIONYX" -PasswordNeverExpires
        Write-Host "  [OK] Created user: $username" -ForegroundColor Green
        Write-Host "  [INFO] Password: $password (CHANGE THIS IN PRODUCTION!)" -ForegroundColor Yellow
    } catch {
        Write-Host "  [ERROR] Failed to create user: $_" -ForegroundColor Red
    }
}

# Ensure user is NOT an admin (remove from Administrators group if present)
try {
    Remove-LocalGroupMember -Group "Administrators" -Member $username -ErrorAction SilentlyContinue
    Write-Host "  [OK] Ensured '$username' is not an Administrator" -ForegroundColor Green
} catch {
    # Not in group, that's fine
}

Write-Host ""

# ============================================================================
# STEP 2: Apply Registry Restrictions (for KioskUser)
# ============================================================================
Write-Host "STEP 2: Applying Registry Restrictions..." -ForegroundColor Yellow

# Get the SID of the kiosk user
$userSID = (Get-LocalUser -Name $username).SID.Value

# Registry path for user policies
$policyPath = "Registry::HKEY_USERS\$userSID\Software\Microsoft\Windows\CurrentVersion\Policies"

Write-Host "  Loading user registry hive..." -ForegroundColor Cyan

# Load the user's NTUSER.DAT if not already loaded
$ntUserPath = "C:\Users\$username\NTUSER.DAT"
if (Test-Path $ntUserPath) {
    reg load "HKU\$userSID" $ntUserPath 2>$null
}

# Create policies if they don't exist
$policies = @(
    @{Path="Explorer"; Values=@{
        "NoRun"=1                    # Disable Run dialog
        "NoControlPanel"=1           # Disable Control Panel
        "NoFileMenu"=1               # Disable File menu in Explorer
        "NoViewContextMenu"=1        # Disable right-click context menu
        "NoDesktop"=0                # Keep desktop visible (optional)
    }},
    @{Path="System"; Values=@{
        "DisableRegistryTools"=1     # Disable Registry Editor
        "DisableCMD"=2               # Disable CMD (2 = disable completely)
        "DisableTaskMgr"=1           # Disable Task Manager
    }}
)

foreach ($policy in $policies) {
    $fullPath = "Registry::HKEY_USERS\$userSID\Software\Microsoft\Windows\CurrentVersion\Policies\$($policy.Path)"
    
    # Create path if it doesn't exist
    if (-not (Test-Path $fullPath)) {
        try {
            New-Item -Path $fullPath -Force | Out-Null
        } catch {
            Write-Host "  [WARN] Could not create: $fullPath" -ForegroundColor Yellow
            continue
        }
    }
    
    foreach ($key in $policy.Values.Keys) {
        try {
            Set-ItemProperty -Path $fullPath -Name $key -Value $policy.Values[$key] -Type DWord -Force
            Write-Host "  [OK] Set $($policy.Path)\$key = $($policy.Values[$key])" -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Could not set ${key}: $_" -ForegroundColor Yellow
        }
    }
}

# Unload the hive
reg unload "HKU\$userSID" 2>$null

Write-Host ""

# ============================================================================
# STEP 3: Configure Group Policy (requires gpedit.msc)
# ============================================================================
Write-Host "STEP 3: Group Policy Recommendations..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Run 'gpedit.msc' as Administrator and configure:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  User Configuration > Administrative Templates > System:" -ForegroundColor White
Write-Host "    - Prevent access to registry editing tools: ENABLED" -ForegroundColor Gray
Write-Host "    - Prevent access to the command prompt: ENABLED" -ForegroundColor Gray
Write-Host "    - Don't run specified Windows applications: (add list)" -ForegroundColor Gray
Write-Host ""
Write-Host "  User Configuration > Administrative Templates > System > Ctrl+Alt+Del Options:" -ForegroundColor White
Write-Host "    - Remove Task Manager: ENABLED" -ForegroundColor Gray
Write-Host "    - Remove Lock Computer: ENABLED" -ForegroundColor Gray
Write-Host "    - Remove Change Password: ENABLED" -ForegroundColor Gray
Write-Host ""
Write-Host "  User Configuration > Administrative Templates > Windows Components > File Explorer:" -ForegroundColor White
Write-Host "    - Remove 'Map Network Drive' and 'Disconnect Network Drive': ENABLED" -ForegroundColor Gray
Write-Host "    - Hide these specified drives in My Computer: (hide C:)" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# STEP 4: Set SIONYX to Auto-Start
# ============================================================================
Write-Host "STEP 4: Auto-Start Configuration..." -ForegroundColor Yellow

$sionyxPath = Read-Host "Enter full path to SIONYX.exe (or press Enter to skip)"

if ($sionyxPath -and (Test-Path $sionyxPath)) {
    # Add to startup for KioskUser
    $startupPath = "C:\Users\$username\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    
    if (-not (Test-Path $startupPath)) {
        New-Item -Path $startupPath -ItemType Directory -Force | Out-Null
    }
    
    $shortcutPath = Join-Path $startupPath "SIONYX.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $sionyxPath
    $shortcut.Save()
    
    Write-Host "  [OK] SIONYX will auto-start for $username" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Auto-start not configured" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# STEP 5: Additional Security Recommendations
# ============================================================================
Write-Host "STEP 5: Additional Security Recommendations..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. BIOS/UEFI: Set password and disable boot from USB/CD" -ForegroundColor White
Write-Host "  2. Windows: Enable Secure Boot" -ForegroundColor White
Write-Host "  3. Consider AppLocker for application whitelisting" -ForegroundColor White
Write-Host "  4. Disable Guest account if enabled" -ForegroundColor White
Write-Host "  5. Remove unnecessary software from the PC" -ForegroundColor White
Write-Host "  6. Keep Windows and apps updated" -ForegroundColor White
Write-Host ""

# ============================================================================
# Done!
# ============================================================================
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Log out and log in as '$username' to test" -ForegroundColor White
Write-Host "  2. Verify restrictions are working" -ForegroundColor White
Write-Host "  3. Apply Group Policy settings via gpedit.msc" -ForegroundColor White
Write-Host ""
Write-Host "To undo these changes, run setup-kiosk-restrictions.ps1 -Undo" -ForegroundColor Yellow
Write-Host ""
