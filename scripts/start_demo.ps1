param(
    [ValidateSet("cloudflared", "ngrok", "none")]
    [string]$Tunnel = "cloudflared",
    [int]$Port = 8000,
    [string]$NgrokDomain = "",
    [string]$NgrokPath = "ngrok",
    [string]$CloudflaredPath = "",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Logs = Join-Path $Root "logs"
$Runtime = Join-Path $Root ".runtime"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

New-Item -ItemType Directory -Force -Path $Logs | Out-Null
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

function Start-ManagedProcess {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$Name
    )

    try {
        return Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru
    }
    catch {
        $startup = ([wmiclass]"Win32_ProcessStartup").CreateInstance()
        $startup.ShowWindow = 0
        $quotedFile = '"' + $FilePath + '"'
        $command = $quotedFile + " " + ($Arguments -join " ")
        $result = ([wmiclass]"Win32_Process").Create($command, $WorkingDirectory, $startup)
        if ($result.ReturnValue -ne 0) {
            throw "Failed to start $Name. ReturnValue=$($result.ReturnValue)"
        }
        return [pscustomobject]@{ Id = $result.ProcessId }
    }
}

function Wait-HttpOk {
    param([string]$Url)

    for ($i = 0; $i -lt 30; $i++) {
        try {
            Invoke-RestMethod -Uri $Url -TimeoutSec 2 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port")
if ($Reload) {
    $uvicornArgs += "--reload"
}

$api = Start-ManagedProcess -FilePath $Python -Arguments $uvicornArgs -WorkingDirectory $Root -Name "uvicorn"
$healthUrl = "http://127.0.0.1:$Port/healthz"
if (-not (Wait-HttpOk $healthUrl)) {
    throw "Local API did not become healthy at $healthUrl"
}

$publicBaseUrl = ""
$tunnelProcess = $null

if ($Tunnel -eq "cloudflared") {
    if (-not $CloudflaredPath) {
        $CloudflaredPath = Join-Path $Root "tools\cloudflared.exe"
    }
    if (-not (Test-Path $CloudflaredPath)) {
        throw "cloudflared.exe not found at $CloudflaredPath. Download it or run with -Tunnel ngrok."
    }

    $cloudflaredLog = Join-Path $Logs "cloudflared.log"
    Remove-Item -Path $cloudflaredLog -Force -ErrorAction SilentlyContinue
    $tunnelArgs = @("tunnel", "--url", "http://127.0.0.1:$Port", "--logfile", $cloudflaredLog, "--loglevel", "info")
    $tunnelProcess = Start-ManagedProcess -FilePath $CloudflaredPath -Arguments $tunnelArgs -WorkingDirectory $Root -Name "cloudflared"

    for ($i = 0; $i -lt 30; $i++) {
        if (Test-Path $cloudflaredLog) {
            $log = Get-Content $cloudflaredLog -Raw
            $match = [regex]::Match($log, "https://[a-z0-9-]+\.trycloudflare\.com")
            if ($match.Success) {
                $publicBaseUrl = $match.Value
                break
            }
        }
        Start-Sleep -Seconds 1
    }
}
elseif ($Tunnel -eq "ngrok") {
    $domainArg = @()
    if ($NgrokDomain) {
        $domainArg = @("--domain=$NgrokDomain")
        $publicBaseUrl = "https://$NgrokDomain"
    }
    $tunnelProcess = Start-ManagedProcess -FilePath $NgrokPath -Arguments (@("http") + $domainArg + @("http://127.0.0.1:$Port")) -WorkingDirectory $Root -Name "ngrok"
}

$callbackUrl = if ($publicBaseUrl) { "$publicBaseUrl/feishu/events" } else { "(check tunnel output and append /feishu/events)" }
$state = [pscustomobject]@{
    api_pid = $api.Id
    tunnel = $Tunnel
    tunnel_pid = if ($tunnelProcess) { $tunnelProcess.Id } else { $null }
    local_health_url = $healthUrl
    public_base_url = $publicBaseUrl
    feishu_callback_url = $callbackUrl
    started_at = (Get-Date).ToString("s")
}
$state | ConvertTo-Json | Set-Content -Path (Join-Path $Runtime "demo.json") -Encoding utf8

Write-Host "Local API started: $healthUrl"
Write-Host "API PID: $($api.Id)"
if ($tunnelProcess) {
    Write-Host "Tunnel PID: $($tunnelProcess.Id)"
}
Write-Host "Feishu callback URL:"
Write-Host $callbackUrl
Write-Host ""
Write-Host "Stop with: .\scripts\stop_demo.ps1"
