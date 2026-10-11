param([string]$Apk = '\\wsl.localhost\Ubuntu\home\pablo\kyf37-android10\out\target\product\kyf37\system\priv-app\Kyf37Home\Kyf37Home.apk')
$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/current-home-install'))
New-Item -ItemType Directory -Force -Path $folder | Out-Null
Copy-Item -LiteralPath $Apk -Destination (Join-Path $folder 'Kyf37Home.apk')
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire current-home 10
try {
 $previous=& $adb -s $serial shell pm path org.kyf37.home
 if($LASTEXITCODE -ne 0 -or -not $previous){throw 'Cannot resolve existing Home'}
 $previousPath=($previous | Select-Object -First 1).Replace('package:','').Trim()
 $backup=Join-Path $folder ('Home-before-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.apk')
 & $adb -s $serial pull $previousPath $backup
 if($LASTEXITCODE -ne 0){throw 'Home backup failed'}
 & $adb -s $serial install -r (Join-Path $folder 'Kyf37Home.apk')
 if($LASTEXITCODE -ne 0){throw 'Home installation failed'}
 & $adb -s $serial shell pm grant org.kyf37.home android.permission.READ_EXTERNAL_STORAGE
 if($LASTEXITCODE -ne 0){throw 'Wallpaper permission grant failed'}
 & $adb -s $serial shell am start -a android.intent.action.MAIN -c android.intent.category.HOME -p org.kyf37.home
 if($LASTEXITCODE -ne 0){throw 'Home launch failed'}
 $installed=& $adb -s $serial shell pm path org.kyf37.home
 $installedPath=($installed | Select-Object -First 1).Replace('package:','').Trim()
 & $adb -s $serial pull $installedPath (Join-Path $folder 'Home-installed.apk')
 if($LASTEXITCODE -ne 0){throw 'Cannot verify installed Home'}
 $expected=(Get-FileHash -LiteralPath (Join-Path $folder 'Kyf37Home.apk') -Algorithm SHA256).Hash
 $actual=(Get-FileHash -LiteralPath (Join-Path $folder 'Home-installed.apk') -Algorithm SHA256).Hash
 if($actual -ne $expected){throw 'Installed APK hash mismatch'}
 & $adb -s $serial shell screencap -p /data/local/tmp/current-home-install.png
 if($LASTEXITCODE -ne 0){throw 'Screenshot capture failed'}
 & $adb -s $serial pull /data/local/tmp/current-home-install.png (Join-Path $folder 'home-live.png')
 if($LASTEXITCODE -ne 0){throw 'Screenshot retrieval failed'}
 @{installed=(Get-Date).ToString('o');sha256=$expected;backup=$backup;installedPath=$installedPath} | ConvertTo-Json | Set-Content (Join-Path $folder 'installation.json')
} finally {& (Join-Path $PSScriptRoot 'phone-lock.ps1') release current-home}
