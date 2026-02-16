<#
.SYNOPSIS
    SIONYX WPF Build Script with Semantic Versioning

.DESCRIPTION
    Build, package, and release the SIONYX WPF kiosk application.
    Handles version bumping, dotnet publish, NSIS installer creation,
    and Firebase Storage upload.

.PARAMETER Increment
    Version increment type: patch (default), minor, or major.

.PARAMETER Version
    Set a specific version (e.g., "2.0.0"). Overrides -Increment.

.PARAMETER NoUpload
    Skip Firebase Storage upload.

.PARAMETER DryRun
    Show what would happen without making changes.

.PARAMETER SkipTests
    Skip running unit tests before build.

.EXAMPLE
    .\build.ps1                    # Patch increment (1.0.0 -> 1.0.1)
    .\build.ps1 -Increment minor  # Minor increment (1.0.1 -> 1.1.0)
    .\build.ps1 -Increment major  # Major increment (1.1.0 -> 2.0.0)
    .\build.ps1 -NoUpload         # Build only
    .\build.ps1 -DryRun           # Preview
#>

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Increment = "patch",

    [string]$Version = "",
    [switch]$NoUpload,
    [switch]$DryRun,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

# =============================================================================
# PATHS
# =============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "src\SionyxKiosk"
$DistDir = Join-Path $ScriptDir "dist"
$VersionFile = Join-Path $ScriptDir "version.json"
$CsprojFile = Join-Path $SrcDir "SionyxKiosk.csproj"

# =============================================================================
# STYLING
# =============================================================================
function Write-Header($text) {
    Write-Host "`n$("=" * 70)" -ForegroundColor Blue
    Write-Host "  $text" -ForegroundColor Blue
    Write-Host "$("=" * 70)`n" -ForegroundColor Blue
}

function Write-Ok($text) { Write-Host "[OK] $text" -ForegroundColor Green }
function Write-Err($text) { Write-Host "[ERROR] $text" -ForegroundColor Red }
function Write-Warn($text) { Write-Host "[WARN] $text" -ForegroundColor Yellow }
function Write-Info($text) { Write-Host "[INFO] $text" -ForegroundColor Cyan }

# =============================================================================
# VERSION MANAGEMENT
# =============================================================================
function Get-VersionData {
    if (Test-Path $VersionFile) {
        return Get-Content $VersionFile -Raw | ConvertFrom-Json
    }
    $default = @{
        version     = "1.0.0"
        major       = 1
        minor       = 0
        patch       = 0
        buildNumber = 0
        lastBuildDate = $null
    }
    $default | ConvertTo-Json | Set-Content $VersionFile
    return $default | ConvertFrom-Json
}

function Save-VersionData($data) {
    $data | ConvertTo-Json -Depth 10 | Set-Content $VersionFile
}

function Step-Version($data, [string]$type, [string]$specific) {
    if ($specific) {
        $parts = $specific -split "\."
        $data.major = [int]$parts[0]
        $data.minor = [int]$parts[1]
        $data.patch = [int]$parts[2]
    }
    else {
        switch ($type) {
            "major" { $data.major++; $data.minor = 0; $data.patch = 0 }
            "minor" { $data.minor++; $data.patch = 0 }
            default { $data.patch++ }
        }
    }
    $data.version = "$($data.major).$($data.minor).$($data.patch)"
    $data.buildNumber++
    $data.lastBuildDate = (Get-Date).ToString("o")
    return $data
}

# =============================================================================
# BUILD STEPS
# =============================================================================
function Test-Dependencies {
    Write-Header "Checking Dependencies"

    $ok = $true

    # .NET SDK
    try {
        $dotnetVersion = dotnet --version
        Write-Ok ".NET SDK $dotnetVersion"
    }
    catch {
        Write-Err ".NET SDK not found"
        $ok = $false
    }

    # NSIS
    $nsisPath = "C:\Program Files (x86)\NSIS"
    if (Test-Path (Join-Path $nsisPath "makensis.exe")) {
        $env:PATH += ";$nsisPath"
        Write-Ok "NSIS found"
    }
    else {
        Write-Err "NSIS not found at $nsisPath"
        $ok = $false
    }

    return $ok
}

function Invoke-Tests {
    Write-Header "Running Tests"

    $testDir = Join-Path $ScriptDir "tests\SionyxKiosk.Tests"
    $result = dotnet test $testDir --verbosity normal 2>&1
    $exitCode = $LASTEXITCODE

    $result | Write-Host

    if ($exitCode -ne 0) {
        Write-Err "Tests FAILED"
        return $false
    }

    Write-Ok "All tests passed"
    return $true
}

function Invoke-Publish {
    Write-Header "Publishing Application"

    # Clean dist
    if (Test-Path $DistDir) { Remove-Item $DistDir -Recurse -Force }

    # Publish single-file, self-contained (WPF does NOT support trimming)
    dotnet publish $CsprojFile `
        -c Release `
        -r win-x64 `
        --self-contained true `
        /p:PublishSingleFile=true `
        /p:IncludeNativeLibrariesForSelfExtract=true `
        /p:EnableCompressionInSingleFile=true `
        /p:DebugType=none `
        /p:DebugSymbols=false `
        -o $DistDir

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Publish failed"
        return $false
    }

    $exe = Join-Path $DistDir "SionyxKiosk.exe"
    if (-not (Test-Path $exe)) {
        Write-Err "Published executable not found"
        return $false
    }

    $size = (Get-Item $exe).Length / 1MB
    Write-Ok "Published: SionyxKiosk.exe ({0:N1} MB)" -f $size
    return $true
}

function New-Installer([string]$ver) {
    Write-Header "Creating Installer v$ver"

    # Copy exe and assets to script dir for NSIS
    $exe = Join-Path $DistDir "SionyxKiosk.exe"
    Copy-Item $exe -Destination $ScriptDir -Force

    # Copy Assets folder if it exists
    $assetsDir = Join-Path $DistDir "Assets"
    if (Test-Path $assetsDir) {
        $dstAssets = Join-Path $ScriptDir "Assets"
        if (Test-Path $dstAssets) { Remove-Item $dstAssets -Recurse -Force }
        Copy-Item $assetsDir -Destination $dstAssets -Recurse -Force
        Write-Ok "Assets copied"
    }

    # Ensure LICENSE.txt exists
    $licensePath = Join-Path $ScriptDir "LICENSE.txt"
    if (-not (Test-Path $licensePath)) {
        "SIONYX Software License`nVersion $ver`nCopyright (c) 2025 SIONYX Technologies" | Set-Content $licensePath
    }

    # Ensure icon exists
    $iconDst = Join-Path $ScriptDir "app-logo.ico"
    if (-not (Test-Path $iconDst)) {
        # Try to find icon in source project
        $iconSrc = Join-Path $SrcDir "app-logo.ico"
        if (Test-Path $iconSrc) {
            Copy-Item $iconSrc $iconDst
        }
        else {
            Write-Warn "app-logo.ico not found; installer may fail"
        }
    }

    # Run NSIS (pipe to Write-Host so output doesn't pollute the function return)
    Push-Location $ScriptDir
    $nsisOutput = & makensis /DVERSION="$ver" installer.nsi 2>&1
    $nsisExit = $LASTEXITCODE
    $nsisOutput | ForEach-Object { Write-Host $_ }
    Pop-Location

    if ($nsisExit -ne 0) {
        Write-Err "NSIS failed"
        return $null
    }

    # Rename installer with version
    $oldName = Join-Path $ScriptDir "SIONYX-Installer.exe"
    $newName = Join-Path $ScriptDir "sionyx-installer-v$ver.exe"
    if (Test-Path $newName) { Remove-Item $newName }
    Rename-Item $oldName $newName

    Write-Ok "Installer created: sionyx-installer-v$ver.exe"

    # Cleanup copied files
    $copiedExe = Join-Path $ScriptDir "SionyxKiosk.exe"
    if (Test-Path $copiedExe) { Remove-Item $copiedExe }
    $copiedAssets = Join-Path $ScriptDir "Assets"
    if (Test-Path $copiedAssets) { Remove-Item $copiedAssets -Recurse -Force }

    return $newName
}

function Invoke-Upload([string]$installerPath, $versionData) {
    Write-Header "Uploading to Firebase Storage"

    $uploadScript = Join-Path $ScriptDir "upload_release.py"
    if (-not (Test-Path $uploadScript)) {
        Write-Err "Upload script not found: $uploadScript"
        return $false
    }

    $ver = $versionData.version
    $buildNum = $versionData.buildNumber

    python $uploadScript $installerPath $ver $buildNum
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Upload failed"
        return $false
    }

    Write-Ok "Upload complete"
    return $true
}

# =============================================================================
# MAIN
# =============================================================================
Write-Header "SIONYX WPF Build System"

$versionData = Get-VersionData
$currentVersion = $versionData.version

# Calculate new version
$newData = $versionData.PSObject.Copy()
$newData = Step-Version $newData $Increment $Version
$newVersion = $newData.version

Write-Host "  Current version: v$currentVersion"
Write-Host "  New version:     v$newVersion ($Increment)"
Write-Host "  Build number:    #$($newData.buildNumber)"
Write-Host "  Output:          sionyx-installer-v$newVersion.exe"
Write-Host ""

if ($DryRun) {
    Write-Warn "DRY RUN - No changes made"
    exit 0
}

# Check dependencies
if (-not (Test-Dependencies)) {
    Write-Err "Missing dependencies"
    exit 1
}

# Run tests
if (-not $SkipTests) {
    if (-not (Invoke-Tests)) {
        Write-Err "Tests failed - aborting build"
        exit 1
    }
}

# Publish
if (-not (Invoke-Publish)) {
    Write-Err "Publish failed"
    exit 1
}

# Create installer
$installerPath = New-Installer $newVersion
if (-not $installerPath) {
    Write-Err "Installer creation failed"
    exit 1
}

# Save version
Save-VersionData $newData
Write-Ok "Version updated to v$newVersion"

# Upload
if (-not $NoUpload) {
    Invoke-Upload $installerPath $newData
}

# Summary
Write-Header "Build Complete!"
Write-Host "  Version:   v$newVersion"
Write-Host "  Build:     #$($newData.buildNumber)"
Write-Host "  Installer: $installerPath"

$size = if (Test-Path $installerPath) { (Get-Item $installerPath).Length / 1MB } else { 0 }
Write-Host "  Size:      $("{0:N1}" -f $size) MB"
