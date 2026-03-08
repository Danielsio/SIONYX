<#
.SYNOPSIS
    Automated semantic release for the SIONYX Kiosk installer.

.DESCRIPTION
    Determines the version bump from conventional commits, builds the
    installer, generates the changelog, tags, and pushes.

    Flow:
      1. Analyze commits since last tag → determine bump type
      2. Create release branch
      3. Build installer (tests + publish + WiX MSI + upload)
      4. Update version.json + CHANGELOG.md
      5. Commit, merge to main, tag, push

.PARAMETER Override
    Force a specific bump type (patch, minor, major), ignoring commits.

.PARAMETER DryRun
    Preview the release without making changes.

.PARAMETER NoPush
    Don't push to remote (for local testing).

.PARAMETER SkipTests
    Skip unit tests during build.

.PARAMETER NoUpload
    Skip Firebase Storage upload.

.EXAMPLE
    .\release.ps1              # Auto-detect from commits
    .\release.ps1 -Override major
    .\release.ps1 -DryRun
#>

param(
    [ValidateSet("", "patch", "minor", "major")]
    [string]$Override = "",

    [switch]$DryRun,
    [switch]$NoPush,
    [switch]$SkipTests,
    [switch]$NoUpload
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = git rev-parse --show-toplevel 2>$null
if (-not $RepoRoot) { Write-Host "[ERROR] Not in a git repo" -ForegroundColor Red; exit 1 }

$KioskDir = Join-Path $RepoRoot "sionyx-kiosk-wpf"
$VersionFile = Join-Path $KioskDir "version.json"

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
    exit 1
}

# ── Pre-flight ──────────────────────────────────────────────────

Write-Header "SIONYX Automated Release"

$branch = (git rev-parse --abbrev-ref HEAD 2>$null)
if ($branch) { $branch = $branch.Trim() }
if ($branch -ne "main") {
    Write-Host "[ERROR] Must be on main branch (current: $branch)" -ForegroundColor Red
    exit 1
}

$dirty = git status --porcelain 2>$null
if ($dirty) { $dirty = $dirty.Trim() }
if ($dirty) {
    Write-Host "[ERROR] Uncommitted changes. Commit or stash first." -ForegroundColor Red
    exit 1
}

Write-Host "Pulling latest main..."
git pull origin main 2>&1 | Out-Host

# ── Step 1: Determine version ──────────────────────────────────

Write-Header "Analyzing Commits"

$getVersionScript = Join-Path $ScriptDir "get-next-version.ps1"
$overrideParam = if ($Override) { @{ Override = $Override } } else { @{} }
$versionInfo = & $getVersionScript @overrideParam

Write-Host "  Last tag:       $($versionInfo.LastTag)"
Write-Host "  Current:        v$($versionInfo.Current)"
Write-Host "  Bump type:      $($versionInfo.Bump) (from $($versionInfo.CommitCount) commits)"
Write-Host "  Next version:   v$($versionInfo.Next)"
Write-Host ""

if ($versionInfo.Commits.Count -gt 0) {
    Write-Host "  Commits included:" -ForegroundColor DarkGray
    foreach ($c in $versionInfo.Commits) {
        $icon = switch ($c.Type) {
            "feat" { if ($c.Breaking) { "!!" } else { "+" } }
            "fix"  { "*" }
            default { "-" }
        }
        Write-Host "    $icon $($c.Message)" -ForegroundColor DarkGray
    }
}

$newVersion = $versionInfo.Next
$branchName = "release/v$newVersion"
$totalSteps = if ($NoPush) { 5 } else { 6 }

if ($DryRun) {
    Write-Host "`n[DRY RUN] Would perform:" -ForegroundColor Yellow
    Write-Host "  1. Create branch: $branchName"
    Write-Host "  2. Build installer v$newVersion"
    Write-Host "  3. Update version.json + CHANGELOG.md"
    Write-Host "  4. Commit release"
    Write-Host "  5. Merge to main + tag v$newVersion"
    if (-not $NoPush) { Write-Host "  6. Push to remote" }
    exit 0
}

# ── Step 2: Create release branch ──────────────────────────────

Write-Step 1 $totalSteps "Creating release branch"

$result = git checkout -b $branchName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] $result" -ForegroundColor Red
    exit 1
}
Write-Host "Created: $branchName" -ForegroundColor Green

# ── Step 3: Build installer ───────────────────────────────────

Write-Step 2 $totalSteps "Building installer v$newVersion"

Push-Location $KioskDir
$buildScript = Join-Path $KioskDir "build.ps1"
$buildParams = @("-ExecutionPolicy", "Bypass", "-File", $buildScript, "-Version", $newVersion)
if ($SkipTests) { $buildParams += "-SkipTests" }
if ($NoUpload) { $buildParams += "-NoUpload" }
& powershell @buildParams
$buildExit = $LASTEXITCODE
Pop-Location

if ($buildExit -ne 0) {
    Abort-Release $branchName "Build failed! Rolling back..."
}
Write-Host "Build completed" -ForegroundColor Green

# ── Step 4: Generate changelog ─────────────────────────────────

Write-Step 3 $totalSteps "Generating changelog"

$changelogScript = Join-Path $ScriptDir "generate-changelog.ps1"
& $changelogScript -Version $newVersion -Commits $versionInfo.Commits

# ── Step 5: Commit ─────────────────────────────────────────────

Write-Step 4 $totalSteps "Committing release"

git add -A 2>$null
git commit -m "release: v$newVersion" 2>$null
Write-Host "Committed release v$newVersion" -ForegroundColor Green

# ── Step 6: Merge to main + tag ────────────────────────────────

Write-Step 5 $totalSteps "Merging to main + creating tag"

git checkout main 2>$null
git merge $branchName --no-ff -m "Merge release v$newVersion" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Merge failed" -ForegroundColor Red
    exit 1
}

git tag "v$newVersion" 2>$null
Write-Host "Merged to main" -ForegroundColor Green
Write-Host "Created tag: v$newVersion" -ForegroundColor Green

# ── Step 7: Push ───────────────────────────────────────────────

if (-not $NoPush) {
    Write-Step 6 $totalSteps "Pushing to remote"

    git push origin main --tags 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "Pushed main + tags" -ForegroundColor Green }
    else { Write-Host "[WARN] Push failed — push manually" -ForegroundColor Yellow }

    git push origin $branchName 2>$null
}

# ── Done ───────────────────────────────────────────────────────

Write-Header "Release v$newVersion complete!"
Write-Host "  Tag:       v$newVersion"
Write-Host "  Bump:      $($versionInfo.Bump)"
Write-Host "  Commits:   $($versionInfo.CommitCount)"
Write-Host "  Branch:    $branchName"
Write-Host "  Changelog: CHANGELOG.md updated"
if ($NoPush) {
    Write-Host "`n  Don't forget to push:" -ForegroundColor Yellow
    Write-Host "    git push origin main --tags"
}
Write-Host ""
