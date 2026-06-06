$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $Root ".runtime\demo.json"

if (-not (Test-Path $StatePath)) {
    Write-Host "No runtime state found."
    exit 0
}

$state = Get-Content $StatePath -Raw | ConvertFrom-Json
$pids = @($state.api_pid, $state.tunnel_pid) | Where-Object { $_ }

foreach ($pidValue in $pids) {
    Stop-Process -Id $pidValue -Force
    Write-Host "Stopped process $pidValue"
}

Remove-Item $StatePath -Force
Write-Host "Demo runtime stopped."
