$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial = '981108631314'
$pack = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/pastel-star-icons'))
$apps = @(
    @{ Package = 'com.android.settings'; New = 'Settings-pastel-star.apk'; Old = 'Settings-before-pastel.apk' },
    @{ Package = 'org.kyf37.phonesettings'; New = 'Kyf37PhoneSettings-pastel-star.apk'; Old = 'Kyf37PhoneSettings-before-pastel.apk' }
)
Add-Type -AssemblyName System.IO.Compression.FileSystem
foreach ($app in $apps) {
    $apk = Join-Path $pack $app.New
    if (-not (Test-Path -LiteralPath $apk)) { throw "Missing compiled APK: $apk" }
    $zip = [IO.Compression.ZipFile]::OpenRead($apk)
    try {
        $icons = @($zip.Entries | Where-Object { $_.FullName -match '^res/drawable-nodpi(?:-v\d+)?/pastel_.*\.png$' })
        if ($icons.Count -lt 14) { throw "Missing pastel resources in $apk" }
    } finally { $zip.Dispose() }
}
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire pastel-settings 10
try {
    foreach ($app in $apps) {
        $backup = Join-Path $pack $app.Old
        if (-not (Test-Path -LiteralPath $backup)) {
            $paths = & $adb -s $serial shell pm path $app.Package
            if ($LASTEXITCODE -ne 0) { throw "Cannot find existing APK for $($app.Package)" }
            $old = ($paths | Select-Object -First 1).Replace('package:', '').Trim()
            & $adb -s $serial pull $old $backup
            if ($LASTEXITCODE -ne 0) { throw 'Backup failed' }
        }
        & $adb -s $serial install -r (Join-Path $pack $app.New)
        if ($LASTEXITCODE -ne 0) { throw "Installation failed: $($app.Package)" }
    }
    & $adb -s $serial shell input keyevent 224
    & $adb -s $serial shell wm dismiss-keyguard
    & $adb -s $serial shell am start -a android.settings.SETTINGS
    Start-Sleep -Seconds 3
    & $adb -s $serial shell screencap -p /data/local/tmp/pastel-settings.png
    & $adb -s $serial pull /data/local/tmp/pastel-settings.png (Join-Path $pack 'phone-settings-main.png')
    if ($LASTEXITCODE -ne 0) { throw 'Settings screenshot failed' }
    & $adb -s $serial shell am start -n org.kyf37.phonesettings/.PhoneSettings
    Start-Sleep -Seconds 2
    & $adb -s $serial shell screencap -p /data/local/tmp/pastel-phone-settings.png
    & $adb -s $serial pull /data/local/tmp/pastel-phone-settings.png (Join-Path $pack 'phone-settings-keypad.png')
    if ($LASTEXITCODE -ne 0) { throw 'Phone settings screenshot failed' }
} finally {
    & (Join-Path $PSScriptRoot 'phone-lock.ps1') release pastel-settings
}
