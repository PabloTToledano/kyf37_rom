param([string]$Apk = (Join-Path $PSScriptRoot '../kyf37-rom/pastel-star-icons/Kyf37Home-pastel-star.apk'))
$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial = '981108631314'
$pack = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/pastel-star-icons'))
if (-not (Test-Path -LiteralPath $Apk)) { throw "Missing compiled launcher: $Apk" }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead([IO.Path]::GetFullPath($Apk))
try {
    $icons = @($zip.Entries | Where-Object { $_.FullName -match '^assets/pastel-star/pastel_.*\.png$' })
    if ($icons.Count -ne 64) { throw "Expected 64 embedded icons, found $($icons.Count)" }
} finally { $zip.Dispose() }
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire pastel-icons 10
try {
    $old = & $adb -s $serial shell pm path org.kyf37.home
    if ($LASTEXITCODE -ne 0) { throw 'Cannot query launcher APK' }
    $backup = Join-Path $pack 'Kyf37Home-before-pastel.apk'
    if (-not (Test-Path -LiteralPath $backup)) {
        $oldPath = ($old | Select-Object -First 1).Replace('package:', '').Trim()
        & $adb -s $serial pull $oldPath $backup
        if ($LASTEXITCODE -ne 0) { throw 'Launcher backup failed' }
    }
    & $adb -s $serial install -r $Apk
    if ($LASTEXITCODE -ne 0) { throw 'Launcher installation failed' }
    & $adb -s $serial shell am start -n org.kyf37.home/.Home
    if ($LASTEXITCODE -ne 0) { throw 'Launcher start failed' }
    Start-Sleep -Seconds 3
    & $adb -s $serial shell screencap -p /data/local/tmp/pastel-star-home.png
    & $adb -s $serial pull /data/local/tmp/pastel-star-home.png (Join-Path $pack 'phone-home.png')
    if ($LASTEXITCODE -ne 0) { throw 'Screenshot capture failed' }
} finally {
    & (Join-Path $PSScriptRoot 'phone-lock.ps1') release pastel-icons
}
