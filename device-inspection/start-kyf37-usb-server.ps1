$ErrorActionPreference = 'Stop'
$taskRuleName = 'KYF37 temporary WSL USB recovery 43240'
if (-not (Get-NetFirewallRule -DisplayName $taskRuleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $taskRuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 43240 -LocalAddress '172.24.48.1' -RemoteAddress '172.24.58.194' -Program 'C:\Program Files\usbipd-win\usbipd.exe' | Out-Null
}
$taskServer = Start-Process -FilePath 'C:\Program Files\usbipd-win\usbipd.exe' -ArgumentList 'server usbipd:Port=43240' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'usbipd-server.out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'usbipd-server.err.log')
$taskServer.Id | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'usbipd-server.pid')
