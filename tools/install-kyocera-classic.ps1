param([switch]$Rollback,[switch]$KeepLock)
$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/kyocera-classic'))
$apps=@(@{Package='org.kyf37.home';Name='Kyf37Home'},@{Package='org.kyf37.phonesettings';Name='Kyf37PhoneSettings'},@{Package='com.android.settings';Name='Settings'})
foreach($app in $apps){$suffix=if($Rollback){'-before.apk'}else{'.apk'};if(-not(Test-Path (Join-Path $folder ($app.Name+$suffix)))){throw "Missing $($app.Name+$suffix)"}}
$state=& (Join-Path $PSScriptRoot 'phone-lock.ps1') status
if($state -like 'LOCKED*' -and $state -notlike 'LOCKED by kyocera-theme *'){throw "Phone busy: $state"}
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire kyocera-theme 30
try {
 if(-not $Rollback -and -not(Test-Path (Join-Path $folder 'theme-before.txt'))){(& $adb -s $serial shell settings get global kyf37_icon_theme).Trim() | Set-Content (Join-Path $folder 'theme-before.txt')}
 foreach($app in $apps){
  $backup=Join-Path $folder ($app.Name+'-before.apk')
  if(-not $Rollback -and -not(Test-Path $backup)){
   $old=(& $adb -s $serial shell pm path $app.Package | Select-Object -First 1)
   if($LASTEXITCODE -ne 0 -or -not $old){throw 'Cannot resolve installed APK'}
   & $adb -s $serial pull $old.Replace('package:','').Trim() $backup
   if($LASTEXITCODE -ne 0){throw 'Backup failed'}
  }
  $apk=if($Rollback){$backup}else{Join-Path $folder ($app.Name+'.apk')}
  & $adb -s $serial install -r -d $apk
  if($LASTEXITCODE -ne 0){throw "Installation failed: $($app.Package)"}
 }
 if($Rollback){
  $old=(Get-Content (Join-Path $folder 'theme-before.txt')).Trim()
  if($old -eq 'null'){& $adb -s $serial shell settings delete global kyf37_icon_theme}else{& $adb -s $serial shell settings put global kyf37_icon_theme $old}
 }else{
  & $adb -s $serial shell settings put global kyf37_icon_theme 3
  if($LASTEXITCODE -ne 0){throw 'Theme selection failed'}
  & $adb -s $serial shell am start -n org.kyf37.home/.WallpaperSetup
  if($LASTEXITCODE -ne 0){throw 'Wallpaper setter could not launch'}
 }
 & $adb -s $serial shell am start -a android.intent.action.MAIN -c android.intent.category.HOME -n org.kyf37.home/.Home
 if($LASTEXITCODE -ne 0){throw 'Home launch failed'}
 # No credential dismissal, reboot, remount or partition flashing.
}finally{if(-not $KeepLock){& (Join-Path $PSScriptRoot 'phone-lock.ps1') release kyocera-theme}}
