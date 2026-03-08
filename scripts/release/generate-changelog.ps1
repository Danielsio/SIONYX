<#
.SYNOPSIS
    Generate or update CHANGELOG.md from conventional commits.

.PARAMETER Version
    The version being released (e.g. "3.5.0").

.PARAMETER Commits
    Array of parsed commit objects from get-next-version.ps1.

.PARAMETER OutputPath
    Path to CHANGELOG.md. Defaults to repo root.
#>

param(
    [Parameter(Mandatory)]
    [string]$Version,

    [Parameter(Mandatory)]
    [object[]]$Commits,

    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $OutputPath) {
    $repoRoot = git rev-parse --show-toplevel 2>$null
    $OutputPath = Join-Path $repoRoot "CHANGELOG.md"
}

$date = (Get-Date).ToString("yyyy-MM-dd")

# Group commits by type
$breaking = $Commits | Where-Object { $_.Breaking }
$features = $Commits | Where-Object { $_.Type -eq "feat" -and -not $_.Breaking }
$fixes    = $Commits | Where-Object { $_.Type -eq "fix" -and -not $_.Breaking }
$others   = $Commits | Where-Object { $_.Type -notin @("feat", "fix") -and -not $_.Breaking -and $_.Type -ne "other" }

$entry = "## [$Version] - $date`n"

if ($breaking) {
    $entry += "`n### Breaking Changes`n"
    foreach ($c in $breaking) {
        $scope = if ($c.Scope) { "**$($c.Scope)**: " } else { "" }
        $entry += "- $scope$($c.Description) ($($c.Hash))`n"
    }
}

if ($features) {
    $entry += "`n### Features`n"
    foreach ($c in $features) {
        $scope = if ($c.Scope) { "**$($c.Scope)**: " } else { "" }
        $entry += "- $scope$($c.Description) ($($c.Hash))`n"
    }
}

if ($fixes) {
    $entry += "`n### Bug Fixes`n"
    foreach ($c in $fixes) {
        $scope = if ($c.Scope) { "**$($c.Scope)**: " } else { "" }
        $entry += "- $scope$($c.Description) ($($c.Hash))`n"
    }
}

if ($others) {
    $entry += "`n### Other`n"
    foreach ($c in $others) {
        $scope = if ($c.Scope) { "**$($c.Scope)**: " } else { "" }
        $entry += "- $scope$($c.Description) ($($c.Hash))`n"
    }
}

# Read existing changelog or create header
if (Test-Path $OutputPath) {
    $existing = Get-Content $OutputPath -Raw
}
else {
    $existing = "# Changelog`n`nAll notable changes to the SIONYX Kiosk installer are documented here.`nThis file is auto-generated from [Conventional Commits](https://www.conventionalcommits.org/).`n"
}

# Insert new entry after the header (first line + blank line)
$headerEnd = $existing.IndexOf("`n`n")
if ($headerEnd -gt 0) {
    $header = $existing.Substring(0, $headerEnd + 2)
    $body = $existing.Substring($headerEnd + 2)
    $updated = $header + "`n" + $entry + "`n" + $body
}
else {
    $updated = $existing + "`n" + $entry
}

Set-Content $OutputPath -Value $updated.TrimEnd() -NoNewline
Write-Host "[OK] CHANGELOG.md updated with v$Version"

return $OutputPath
