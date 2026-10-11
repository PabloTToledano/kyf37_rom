param()
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$apk=Join-Path $root 'device-inspection/outer-animation/Kyf37OuterScreen-animation.apk'
if(-not(Test-Path -LiteralPath $apk)){throw 'Build/package Kyf37OuterScreen first.'}
& "$PSScriptRoot/phone-lock.ps1" acquire outer-badapple-install 15
try {
 & $adb -s 981108631314 root
 Start-Sleep -Seconds 4
 $path=& $adb -s 981108631314 shell pm path org.kyf37.subdisplay
 if($LASTEXITCODE -ne 0){throw 'Cannot find installed outer-screen APK.'}
 $old=($path | Select-Object -First 1).Trim() -replace '^package:',''
 $backup=Join-Path $root ('device-inspection/outer-animation/OuterScreen-before-'+(Get-Date -Format yyyyMMdd-HHmmss)+'.apk')
 & $adb -s 981108631314 pull $old $backup
 if($LASTEXITCODE -ne 0){throw 'Rollback copy failed.'}
 & $adb -s 981108631314 install -r $apk
 if($LASTEXITCODE -ne 0){throw 'Outer-screen installation failed.'}
 & $adb -s 981108631314 shell am startservice -n org.kyf37.subdisplay/.OuterScreenService
 if($LASTEXITCODE -ne 0){throw 'Outer-screen service did not start.'}
 Write-Output 'Installed. Closed lid: hold side key 0.8 seconds for Bad Apple; press once to stop.'
} finally { & "$PSScriptRoot/phone-lock.ps1" release outer-badapple-install }
