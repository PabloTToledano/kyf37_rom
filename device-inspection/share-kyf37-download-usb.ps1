$ErrorActionPreference = 'Stop'
$taskLog = Join-Path $PSScriptRoot 'share-kyf37-download-usb.log'
try {
    Start-Service -Name usbipd
    & 'C:\Program Files\usbipd-win\usbipd.exe' bind --hardware-id '0482:0a7f' --force *> $taskLog
    if ($LASTEXITCODE -ne 0) { throw "usbipd bind failed with $LASTEXITCODE" }
    'KYF37_DOWNLOAD_USB_SHARED' | Add-Content -LiteralPath $taskLog
} catch {
    $_ | Out-String | Add-Content -LiteralPath $taskLog
    exit 1
}
