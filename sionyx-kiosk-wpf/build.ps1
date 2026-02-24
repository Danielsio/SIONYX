<#
.SYNOPSIS
    SIONYX WPF Build Script with Semantic Versioning

.DESCRIPTION
    Build, package, and release the SIONYX WPF kiosk application.
    Handles version bumping, dotnet publish, WiX MSI installer creation,
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

$ErrorActionPreference = "Continue"

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

    # WiX SDK is pulled via NuGet (WixToolset.Sdk) - no external install needed
    Write-Ok "WiX Toolset (NuGet SDK - restored automatically)"

    return $ok
}

function Invoke-Tests {
    Write-Header "Running Tests"

    $testDir = Join-Path $ScriptDir "tests\SionyxKiosk.Tests"
    dotnet test $testDir --filter "Category!=Destructive" --verbosity normal 2>&1 | Out-Host
    $exitCode = $LASTEXITCODE

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
    Write-Header "Creating Installer v$ver (WiX MSI)"

    $installerDir = Join-Path $ScriptDir "installer"
    $wixProj = Join-Path $installerDir "SionyxInstaller.wixproj"

    if (-not (Test-Path $wixProj)) {
        Write-Err "WiX project not found: $wixProj"
        return $null
    }

    # Ensure icon exists at script root (referenced by WiX SourceDir)
    $iconDst = Join-Path $ScriptDir "app-logo.ico"
    if (-not (Test-Path $iconDst)) {
        $iconSrc = Join-Path $SrcDir "app-logo.ico"
        if (Test-Path $iconSrc) {
            Copy-Item $iconSrc $iconDst
        }
        else {
            Write-Warn "app-logo.ico not found; installer may fail"
        }
    }

    # Build the MSI via dotnet (WiX SDK restores automatically)
    $publishDir = [System.IO.Path]::GetFullPath($DistDir)
    $sourceDir = [System.IO.Path]::GetFullPath($ScriptDir)

    $wixOutput = dotnet build $wixProj `
        -c Release `
        -p:Platform=x64 `
        -p:ProductVersion=$ver `
        -p:PublishDir=$publishDir `
        -p:SourceDir=$sourceDir `
        2>&1
    $wixExit = $LASTEXITCODE
    $wixOutput | ForEach-Object { Write-Host $_ }

    if ($wixExit -ne 0) {
        Write-Err "WiX build failed"
        return $null
    }

    # Find the built MSI
    $msiDir = Join-Path $installerDir "bin\x64\Release"
    $msiFile = Get-ChildItem -Path $msiDir -Filter "*.msi" -ErrorAction SilentlyContinue | Select-Object -First 1

    if (-not $msiFile) {
        Write-Err "MSI output not found in $msiDir"
        return $null
    }

    # Copy MSI to script dir with versioned name
    $newName = Join-Path $ScriptDir "sionyx-installer-v$ver.msi"
    if (Test-Path $newName) { Remove-Item $newName }
    Copy-Item $msiFile.FullName $newName

    Write-Ok "Installer created: sionyx-installer-v$ver.msi"
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
Write-Host "  Output:          sionyx-installer-v$newVersion.msi"
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
$uploaded = $false
if (-not $NoUpload) {
    $uploaded = Invoke-Upload $installerPath $newData
}

# Summary
Write-Header "Build Complete!"
Write-Host "  Version:   v$newVersion"
Write-Host "  Build:     #$($newData.buildNumber)"
Write-Host "  Installer: $installerPath"

$size = if (Test-Path $installerPath) { (Get-Item $installerPath).Length / 1MB } else { 0 }
Write-Host "  Size:      $("{0:N1}" -f $size) MB"

# Cleanup: remove local installer after successful upload
if ($uploaded -and (Test-Path $installerPath)) {
    Remove-Item $installerPath -Force
    Write-Ok "Local installer deleted after upload"
}
