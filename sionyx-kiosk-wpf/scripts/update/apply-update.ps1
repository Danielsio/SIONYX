<#
  SIONYX auto-update applier.

  Runs as LocalSystem via the "SIONYX Update" scheduled task (registered by the
  installer). The kiosk app (a non-admin user) cannot run an elevated installer
  without a UAC prompt, so instead it stages an update request and this script —
  running as SYSTEM — re-verifies the SHA-256 and installs the MSI silently.

  Idempotent: the request is consumed on success so the task never re-installs it.
  Picks up work on every trigger (boot + 15-min repetition + on-demand).
#>
[CmdletBinding()]
param(
    [string]$UpdateDir = (Join-Path $env:ProgramData 'SIONYX\update')
)

$ErrorActionPreference = 'Stop'
$pending = Join-Path $UpdateDir 'pending.json'
$logFile = Join-Path $UpdateDir 'update.log'

function Write-Log($msg) {
    $line = '{0:yyyy-MM-dd HH:mm:ss}  {1}' -f (Get-Date), $msg
    Write-Host $line
    try { Add-Content -Path $logFile -Value $line -ErrorAction SilentlyContinue } catch { }
}

if (-not (Test-Path $pending)) { Write-Host 'No pending update.'; exit 0 }

try {
    if (-not (Test-Path $UpdateDir)) { New-Item -ItemType Directory -Path $UpdateDir -Force | Out-Null }

    $req = Get-Content $pending -Raw | ConvertFrom-Json
    $msi = [string]$req.MsiPath
    $expected = ([string]$req.Sha256).ToLower()

    if ([string]::IsNullOrWhiteSpace($msi) -or -not (Test-Path $msi)) {
        Write-Log "[FAIL] MSI not found: $msi"
        Rename-Item $pending "$pending.rejected" -Force
        exit 1
    }

    if ($expected) {
        $actual = (Get-FileHash -Path $msi -Algorithm SHA256).Hash.ToLower()
        if ($actual -ne $expected) {
            Write-Log "[FAIL] SHA-256 mismatch (expected $expected, got $actual) - refusing to install"
            Rename-Item $pending "$pending.rejected" -Force
            exit 2
        }
        Write-Log "[OK] SHA-256 verified: $actual"
    }
    else {
        Write-Log '[WARN] No SHA-256 in request - installing unverified'
    }

    $msiLog = Join-Path $UpdateDir 'msiexec.log'
    Write-Log "[..] Installing $msi"
    $p = Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qn /norestart /l*v `"$msiLog`"" -Wait -PassThru

    # 0 = success, 3010 = success but a reboot is required.
    if ($p.ExitCode -eq 0 -or $p.ExitCode -eq 3010) {
        Write-Log "[OK] Install succeeded (exit $($p.ExitCode))"
        Remove-Item $pending -Force -ErrorAction SilentlyContinue
        exit 0
    }

    Write-Log "[FAIL] msiexec exit $($p.ExitCode) - see $msiLog"
    Rename-Item $pending "$pending.failed" -Force
    exit $p.ExitCode
}
catch {
    Write-Log "[FAIL] $($_.Exception.Message)"
    exit 1
}
