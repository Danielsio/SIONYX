# SIONYX Build Script for PowerShell
# ==================================

param(
    [switch]$ExecutableOnly,
    [switch]$SkipWeb,
    [switch]$ForceWeb,
    [switch]$SkipInstaller,
    [switch]$Upload,
    [switch]$UploadInstaller,
    [string]$Bucket = "sionyx-19636",
    [switch]$Help
)

function Show-Help {
    Write-Host "SIONYX Build Script" -ForegroundColor Blue
    Write-Host "===================" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Usage: .\build.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -ExecutableOnly    Only create executable, skip web build and installer" -ForegroundColor White
    Write-Host "  -SkipWeb          Skip web application build" -ForegroundColor White
    Write-Host "  -ForceWeb         Force rebuild of web application" -ForegroundColor White
    Write-Host "  -SkipInstaller    Skip NSIS installer creation" -ForegroundColor White
    Write-Host "  -Upload           Upload executable to Firebase Storage" -ForegroundColor White
    Write-Host "  -UploadInstaller  Also upload installer to Firebase Storage" -ForegroundColor White
    Write-Host "  -Bucket NAME      Firebase Storage bucket name (default: sionyx-19636)" -ForegroundColor White
    Write-Host "  -Help             Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\build.ps1                           # Full build (web + executable + installer)" -ForegroundColor White
    Write-Host "  .\build.ps1 -ExecutableOnly           # Only create executable" -ForegroundColor White
    Write-Host "  .\build.ps1 -SkipWeb                  # Skip web build, create executable + installer" -ForegroundColor White
    Write-Host "  .\build.ps1 -Upload                   # Build, upload to Firebase, clean local files" -ForegroundColor White
    Write-Host "  .\build.ps1 -Upload -UploadInstaller  # Build, upload both files, clean local files" -ForegroundColor White
    Write-Host ""
    Write-Host "Setup Firebase Storage:" -ForegroundColor Cyan
    Write-Host "  python setup_firebase.py              # Interactive Firebase setup" -ForegroundColor White
    Write-Host ""
}

# Show help if requested or no parameters
if ($Help -or (-not $ExecutableOnly -and -not $SkipWeb -and -not $ForceWeb -and -not $SkipInstaller -and -not $Upload -and -not $UploadInstaller)) {
    Show-Help
    exit 0
}

Write-Host "SIONYX Build Script" -ForegroundColor Blue
Write-Host "===================" -ForegroundColor Blue
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "src/main.py")) {
    Write-Host "ERROR: Not in SIONYX project directory" -ForegroundColor Red
    Write-Host "Please run this script from the SIONYX project root" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Build command arguments
$buildArgs = @()

if ($ExecutableOnly) { $buildArgs += "--executable-only" }
if ($SkipWeb) { $buildArgs += "--skip-web" }
if ($ForceWeb) { $buildArgs += "--force-web" }
if ($SkipInstaller) { $buildArgs += "--skip-installer" }
if ($Upload) { $buildArgs += "--upload" }
if ($UploadInstaller) { $buildArgs += "--upload-installer" }
if ($Bucket -ne "sionyx-19636") { $buildArgs += "--bucket"; $buildArgs += $Bucket }

# Run the build script
Write-Host "Running build process..." -ForegroundColor Cyan
Write-Host ""

try {
    if ($buildArgs.Count -gt 0) {
        python build.py @buildArgs
    } else {
        python build.py
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Build completed successfully!" -ForegroundColor Green
        if ($Upload) {
            Write-Host "Files uploaded to Firebase Storage and local files cleaned up." -ForegroundColor Cyan
        } else {
            Write-Host "Check the 'distribution' folder for your installer." -ForegroundColor Cyan
        }
    } else {
        Write-Host ""
        Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "Build script failed: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Read-Host "Press Enter to exit"