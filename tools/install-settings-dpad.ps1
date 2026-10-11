param([string]$Name='settings-dpad')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$dir=Join-Path $root 'kyf37-rom/settings-dpad'
if(-not(Test-Path "$dir/Settings.apk")){throw 'Build the corrected Settings.apk first'}
& "$PSScriptRoot/phone-lock.ps1" acquire $Name 15
try {
    if(-not(Test-Path "$dir/Settings-before.apk")) {
        $path=(& $adb -s 981108631314 shell pm path com.android.settings | Select-Object -First 1).Trim() -replace '^package:',''
        if($LASTEXITCODE -ne 0 -or -not $path){throw 'Cannot locate installed Settings'}
        & $adb -s 981108631314 pull $path "$dir/Settings-before.apk"
        if($LASTEXITCODE -ne 0){throw 'Backup failed'}
    }
    & $adb -s 981108631314 install -r -d "$dir/Settings.apk"
    if($LASTEXITCODE -ne 0){throw 'Settings installation failed'}
} finally { & "$PSScriptRoot/phone-lock.ps1" release $Name }
