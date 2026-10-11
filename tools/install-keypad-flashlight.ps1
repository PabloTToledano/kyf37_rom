param([switch]$KeepLegacy,[switch]$SkipInstall)
$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/keypad-flashlight'))
$global:LASTEXITCODE=0
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire keypad-flashlight 10
if($LASTEXITCODE -ne 0){throw 'Phone is in use'}
try {
 if(-not $SkipInstall){
  foreach($app in @(@{Name='Kyf37Home';Package='org.kyf37.home'},@{Name='MobileLight';Package='jp.kyocera.mobilelight'})){
   $backup=Join-Path $folder ($app.Name+'-before-keypad-flashlight.apk')
   if(-not(Test-Path -LiteralPath $backup)){
    $line=& $adb -s $serial shell pm path $app.Package
    $path=($line | Select-Object -First 1).Replace('package:','').Trim()
    & $adb -s $serial pull $path $backup
    if($LASTEXITCODE -ne 0){throw 'Backup failed'}
   }
  }
  foreach($name in @('Kyf37Flashlight','Kyf37Home')){
   & $adb -s $serial install -r (Join-Path $folder ($name+'.apk'))
   if($LASTEXITCODE -ne 0){throw "Install failed: $name"}
  }
  & $adb -s $serial shell pm grant org.kyf37.flashlight android.permission.CAMERA
  if($LASTEXITCODE -ne 0){throw 'Camera torch permission grant failed'}
 }
 if(-not $KeepLegacy){
  & $adb -s $serial shell pm path org.kyf37.flashlight
  if($LASTEXITCODE -ne 0){throw 'Replacement is not installed; legacy app retained'}
  $old=& $adb -s $serial shell pm list packages --user 0 jp.kyocera.mobilelight
  if($old -match 'package:jp.kyocera.mobilelight'){
   & $adb -s $serial shell am force-stop jp.kyocera.mobilelight
   & $adb -s $serial shell pm uninstall --user 0 jp.kyocera.mobilelight
   if($LASTEXITCODE -ne 0){throw 'Legacy removal failed'}
  }
 }
 & $adb -s $serial shell input keyevent 224
 & $adb -s $serial shell wm dismiss-keyguard
 & $adb -s $serial shell am start --activity-clear-top -n org.kyf37.flashlight/.Flashlight
}finally{& (Join-Path $PSScriptRoot 'phone-lock.ps1') release keypad-flashlight}
