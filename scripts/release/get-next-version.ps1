<#
.SYNOPSIS
    Determine the next semantic version from conventional commits.

.DESCRIPTION
    Analyzes git commits since the last version tag (v*) and applies
    Conventional Commits rules to determine the next version bump:
      - feat!: / BREAKING CHANGE → MAJOR
      - feat:                     → MINOR
      - fix:                      → PATCH
    Falls back to PATCH if no conventional commits are found.

.PARAMETER Override
    Force a specific bump type, ignoring commit analysis.

.OUTPUTS
    PSCustomObject with: current, next, bump, commits (array of parsed commits)
#>

param(
    [ValidateSet("", "patch", "minor", "major")]
    [string]$Override = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) { throw "Not inside a git repository" }

$versionFile = Join-Path $repoRoot "sionyx-kiosk-wpf\version.json"
if (-not (Test-Path $versionFile)) { throw "version.json not found at $versionFile" }

$versionData = Get-Content $versionFile -Raw | ConvertFrom-Json

# Highest existing vX.Y.Z tag = the released version. (git describe returns the
# NEAREST ancestor tag, which goes backwards when an older-numbered tag sits on
# a newer commit — exactly what happened after rollbacks deleted newer tags.)
$lastTag = git tag -l 'v*' 2>$null |
    Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } |
    Sort-Object { [version]($_.TrimStart('v')) } |
    Select-Object -Last 1
$range = if ($lastTag) { "$lastTag..HEAD" } else { "HEAD" }

# Current version = the last tag (source of truth). Fall back to version.json only
# for the very first release (no tags yet). Using tags means the release workflow
# never has to push a version-bump commit to the protected main branch.
$currentVersion = if ($lastTag) { $lastTag.TrimStart('v') } else { $versionData.version }

# Get commits since last tag (one-line format: <hash> <message>)
$rawCommits = git log $range --pretty=format:"%H %s" 2>$null
if (-not $rawCommits) { $rawCommits = @() }
if ($rawCommits -is [string]) { $rawCommits = @($rawCommits) }

# Parse conventional commits
$bump = "none"
$parsed = @()

foreach ($line in $rawCommits) {
    if (-not $line.Trim()) { continue }

    $hash = $line.Substring(0, 40)
    $msg = $line.Substring(41)

    $type = "other"
    $scope = ""
    $breaking = $false
    $description = $msg

    # Match: type(scope)!: description  OR  type!: description  OR  type(scope): description  OR  type: description
    if ($msg -match '^(\w+)(?:\(([^)]+)\))?(!)?\s*:\s*(.+)$') {
        $type = $Matches[1].ToLower()
        $scope = if ($Matches[2]) { $Matches[2] } else { "" }
        $breaking = [bool]$Matches[3]
        $description = $Matches[4]
    }

    # Check commit body for BREAKING CHANGE footer
    $body = git log -1 --pretty=format:"%b" $hash 2>$null
    if ($body -match 'BREAKING[ -]CHANGE') { $breaking = $true }

    $parsed += [PSCustomObject]@{
        Hash        = $hash.Substring(0, 8)
        Type        = $type
        Scope       = $scope
        Breaking    = $breaking
        Description = $description
        Message     = $msg
    }

    if ($breaking)         { $bump = "major" }
    elseif ($type -eq "feat" -and $bump -ne "major") { $bump = "minor" }
    elseif ($type -eq "fix"  -and $bump -notin @("major", "minor")) { $bump = "patch" }
}

if ($bump -eq "none") { $bump = "patch" }
if ($Override) { $bump = $Override }

# Calculate next version FROM THE TAG, not version.json. version.json is never
# committed back (main is protected), so bumping from it froze the math at one
# fixed version: every feat-run computed the same vX.Y.0, collided with the
# existing release, and the failure rollback then DELETED that release.
$cur = [version]$currentVersion
$major = $cur.Major
$minor = $cur.Minor
$patch = $cur.Build

switch ($bump) {
    "major" { $major++; $minor = 0; $patch = 0 }
    "minor" { $minor++; $patch = 0 }
    "patch" { $patch++ }
}

$nextVersion = "$major.$minor.$patch"

# Collision guard (belt & braces): never propose a version whose tag already
# exists — bump patch until the number is free.
while (git tag -l "v$nextVersion" 2>$null) {
    $patch++
    $nextVersion = "$major.$minor.$patch"
}

$result = [PSCustomObject]@{
    Current     = $currentVersion
    Next        = $nextVersion
    Bump        = $bump
    Major       = $major
    Minor       = $minor
    Patch       = $patch
    BuildNumber = [int]$versionData.buildNumber + 1
    LastTag     = if ($lastTag) { $lastTag } else { "(none)" }
    CommitCount = $parsed.Count
    Commits     = $parsed
}

return $result
