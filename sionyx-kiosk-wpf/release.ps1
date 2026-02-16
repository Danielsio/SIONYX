<#
.SYNOPSIS
    Atomic release: branch → build → commit → merge → tag → push

.DESCRIPTION
    Version is only bumped AFTER a successful build.
    On failure everything is rolled back.

.PARAMETER Increment
    patch (default), minor, or major.

.PARAMETER DryRun
    Preview what would happen without making changes.

.PARAMETER NoPush
    Don't push to remote (for local testing).

.EXAMPLE
    .\release.ps1 -Increment patch   # 3.0.0 → 3.0.1
    .\release.ps1 -Increment minor   # 3.0.0 → 3.1.0
    .\release.ps1 -Increment major   # 3.0.0 → 4.0.0
    .\release.ps1 -DryRun            # Preview
#>

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Increment = "patch",

    [switch]$DryRun,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VersionFile = Join-Path $ScriptDir "version.json"

# ── Helpers ───────────────────────────────────────────────────────

function Write-Header($text) {
    Write-Host "`n$("=" * 60)" -ForegroundColor Blue
    Write-Host "  $text" -ForegroundColor Blue
    Write-Host "$("=" * 60)`n" -ForegroundColor Blue
}

function Write-Step($step, $total, $text) {
    Write-Host "`n[$step/$total] $text" -ForegroundColor Cyan
    Write-Host ("-" * 50) -ForegroundColor DarkGray
}

function Abort-Release($branchName, $reason) {
    Write-Host "`n[ABORT] $reason" -ForegroundColor Red
    git checkout main 2>$null
    git branch -D $branchName 2>$null
    Write-Host "Cleaned up branch: $branchName" -ForegroundColor Yellow
    Write-Host "No version changes were made."
    exit 1
}

function Get-BumpedVersion($data, [string]$type) {
    $major = [int]$data.major
    $minor = [int]$data.minor
    $patch = [int]$data.patch

    switch ($type) {
        "major" { $major++; $minor = 0; $patch = 0 }
        "minor" { $minor++; $patch = 0 }
        default { $patch++ }
    }

    $data.major = $major
    $data.minor = $minor
    $data.patch = $patch
    $data.version = "$major.$minor.$patch"
    $data.buildNumber = [int]$data.buildNumber + 1
    $data.lastBuildDate = (Get-Date).ToString("o")
    return $data
}

# ── Pre-flight checks ────────────────────────────────────────────

Write-Header "ATOMIC $($Increment.ToUpper()) Release"

$branch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($branch -ne "main") {
    Write-Host "[ERROR] Must be on main branch (current: $branch)" -ForegroundColor Red
    exit 1
}

$dirty = (git status --porcelain 2>$null).Trim()
if ($dirty) {
    Write-Host "[ERROR] Uncommitted changes. Commit or stash first." -ForegroundColor Red
    exit 1
}

Write-Host "Pulling latest main..."
git pull origin main 2>$null

# ── Calculate new version ─────────────────────────────────────────

$versionData = Get-Content $VersionFile -Raw | ConvertFrom-Json
$oldVersion = $versionData.version
$newData = $versionData.PSObject.Copy()
$newData = Get-BumpedVersion $newData $Increment
$newVersion = $newData.version
$branchName = "release/$newVersion"

Write-Host "Version: v$oldVersion -> v$newVersion"
Write-Host "Branch:  $branchName"

$totalSteps = if ($NoPush) { 4 } else { 5 }

if ($DryRun) {
    Write-Host "`n[DRY RUN] No changes made." -ForegroundColor Yellow
    Write-Host "  1. Create branch: $branchName"
    Write-Host "  2. Build installer v$newVersion"
    Write-Host "  3. Commit version bump"
    Write-Host "  4. Merge to main + tag v$newVersion"
    if (-not $NoPush) { Write-Host "  5. Push to remote" }
    exit 0
}

# ── Step 1: Create release branch ─────────────────────────────────

Write-Step 1 $totalSteps "Creating release branch"

$result = git checkout -b $branchName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] $result" -ForegroundColor Red
    exit 1
}
Write-Host "Created: $branchName" -ForegroundColor Green

# ── Step 2: Build installer ───────────────────────────────────────

Write-Step 2 $totalSteps "Building installer v$newVersion"

Push-Location $ScriptDir
powershell -ExecutionPolicy Bypass -File build.ps1 -Version $newVersion
$buildExit = $LASTEXITCODE
Pop-Location

if ($buildExit -ne 0) {
    Abort-Release $branchName "Build failed! Rolling back..."
}
Write-Host "Build completed" -ForegroundColor Green

# ── Step 3: Commit ────────────────────────────────────────────────

Write-Step 3 $totalSteps "Committing version bump"

git add -A 2>$null
git commit -m "release: v$newVersion" 2>$null
Write-Host "Committed release v$newVersion" -ForegroundColor Green

# ── Step 4: Merge to main + tag ──────────────────────────────────

Write-Step 4 $totalSteps "Merging to main + creating tag"

git checkout main 2>$null
git merge $branchName --no-ff -m "Merge release v$newVersion" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Merge failed" -ForegroundColor Red
    exit 1
}

git tag "v$newVersion" 2>$null
Write-Host "Merged to main" -ForegroundColor Green
Write-Host "Created tag: v$newVersion" -ForegroundColor Green

# ── Step 5: Push ──────────────────────────────────────────────────

if (-not $NoPush) {
    Write-Step 5 $totalSteps "Pushing to remote"

    git push origin main --tags 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "Pushed main + tags" -ForegroundColor Green }
    else { Write-Host "[WARN] Push main failed — push manually" -ForegroundColor Yellow }

    git push origin $branchName 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "Pushed $branchName" -ForegroundColor Green }
    else { Write-Host "[WARN] Push branch failed — push manually" -ForegroundColor Yellow }
}

# ── Done ──────────────────────────────────────────────────────────

Write-Header "Release v$newVersion complete!"
Write-Host "  Tag:    v$newVersion"
Write-Host "  Branch: $branchName"
if ($NoPush) {
    Write-Host "`n  Don't forget to push:" -ForegroundColor Yellow
    Write-Host "    git push origin main --tags"
    Write-Host "    git push origin $branchName"
}
Write-Host ""
