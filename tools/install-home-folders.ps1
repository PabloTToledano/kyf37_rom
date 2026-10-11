param([switch]$Rollback)
$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/home-folders'))
$apk=Join-Path $folder $(if($Rollback){'Kyf37Home-before.apk'}else{'Kyf37Home.apk'})
if(-not(Test-Path -LiteralPath $apk)){throw "Missing APK: $apk"}
$state=& (Join-Path $PSScriptRoot 'phone-lock.ps1') status
if($state -like 'LOCKED*'){throw "Phone busy: $state. Retry after its owner releases it."}
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire home-folders 10
try {
 $backup=Join-Path $folder 'Kyf37Home-before.apk'
 if(-not $Rollback -and -not(Test-Path -LiteralPath $backup)) {
  $old=(& $adb -s $serial shell pm path org.kyf37.home | Select-Object -First 1)
  if($LASTEXITCODE -ne 0 -or -not $old){throw 'Cannot resolve installed launcher'}
  & $adb -s $serial pull $old.Replace('package:','').Trim() $backup
  if($LASTEXITCODE -ne 0){throw 'Launcher backup failed'}
 }
 & $adb -s $serial install -r -d $apk
 if($LASTEXITCODE -ne 0){throw 'Launcher installation failed'}
 & $adb -s $serial shell am start -a android.intent.action.MAIN -c android.intent.category.HOME -n org.kyf37.home/.Home
 if($LASTEXITCODE -ne 0){throw 'Launcher launch failed'}
 # Does not dismiss keyguard or enter credentials. No system remount is needed.
 & $adb -s $serial shell pm path org.kyf37.home
} finally { & (Join-Path $PSScriptRoot 'phone-lock.ps1') release home-folders }
