param([string]$Name='outer-settings-install')
# Live-install the outer-screen timeout/settings build (app updates only; no partition is flashed).
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$apks=@(
 @{pkg='org.kyf37.subdisplay';  file=(Join-Path $root 'device-inspection/outer-animation/Kyf37OuterScreen-settings.apk')},
 @{pkg='org.kyf37.phonesettings';file=(Join-Path $root 'device-inspection/outer-animation/Kyf37PhoneSettings-outer.apk')},
 @{pkg='com.android.settings';  file=(Join-Path $root 'device-inspection/outer-animation/Settings-outer.apk')})
foreach($a in $apks){ if(-not(Test-Path -LiteralPath $a.file)){throw "Missing $($a.file)"} }
& "$PSScriptRoot/phone-lock.ps1" acquire $Name 15
try {
 & $adb -s 981108631314 root | Out-Null
 Start-Sleep -Seconds 4
 foreach($a in $apks){
  $path=(& $adb -s 981108631314 shell pm path $a.pkg | Select-Object -First 1).Trim() -replace '^package:',''
  $backup=Join-Path $root ("device-inspection/outer-animation/"+$a.pkg+"-before-outer-settings.apk")
  if(-not(Test-Path $backup)){ & $adb -s 981108631314 pull $path $backup | Out-Null }
  & $adb -s 981108631314 install -r $a.file
  if($LASTEXITCODE -ne 0){throw "Install failed: $($a.pkg)"}
 }
 & $adb -s 981108631314 shell am startservice -n org.kyf37.subdisplay/.OuterScreenService
 Write-Output 'Installed. Settings -> Outer screen (Phone settings row 16). Keys: Settings.Global kyf37_outer_*'
} finally { & "$PSScriptRoot/phone-lock.ps1" release $Name }
