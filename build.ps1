# SIONYX Build Script for PowerShell
# ==================================

Write-Host "SIONYX Build Script" -ForegroundColor Blue
Write-Host "===================" -ForegroundColor Blue
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "src/main.py")) {
    Write-Host "❌ ERROR: Not in SIONYX project directory" -ForegroundColor Red
    Write-Host "Please run this script from the SIONYX project root" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Show usage if help requested
if ($args -contains "--help") {
    Write-Host "Usage: .\build.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  --executable-only    Only create executable, skip web build and installer" -ForegroundColor White
    Write-Host "  --skip-web          Skip web application build" -ForegroundColor White
    Write-Host "  --force-web         Force rebuild of web application" -ForegroundColor White
    Write-Host "  --skip-installer    Skip NSIS installer creation" -ForegroundColor White
    Write-Host "  --help              Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\build.ps1                    # Full build (web + executable + installer)" -ForegroundColor White
    Write-Host "  .\build.ps1 --executable-only  # Only create executable" -ForegroundColor White
    Write-Host "  .\build.ps1 --skip-web         # Skip web build, create executable + installer" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

# Run the build script
Write-Host "Running build process..." -ForegroundColor Cyan
Write-Host ""

try {
    python build.py $args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
        Write-Host "Check the 'distribution' folder for your installer." -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Build failed! Check the error messages above." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Build script failed: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Read-Host "Press Enter to exit"
