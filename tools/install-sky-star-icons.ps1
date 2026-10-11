$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/sky-star-icons'))
$apps=@(
 @{Package='org.kyf37.home';Name='Kyf37Home'},
 @{Package='org.kyf37.phonesettings';Name='Kyf37PhoneSettings'},
 @{Package='com.android.settings';Name='Settings'}
)
foreach($app in $apps){if(-not(Test-Path -LiteralPath (Join-Path $folder ($app.Name+'.apk')))){throw "Missing $($app.Name).apk"}}
$global:LASTEXITCODE=0
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire sky-star-icons 10
if($LASTEXITCODE -ne 0){throw 'Phone is in use'}
try {
 foreach($app in $apps){
  $backup=Join-Path $folder ($app.Name+'-before-sky-star.apk')
  if(-not(Test-Path -LiteralPath $backup)){
   $old=(& $adb -s $serial shell pm path $app.Package | Select-Object -First 1).Replace('package:','').Trim()
   & $adb -s $serial pull $old $backup
   if($LASTEXITCODE -ne 0){throw 'APK backup failed'}
  }
  & $adb -s $serial install -r (Join-Path $folder ($app.Name+'.apk'))
  if($LASTEXITCODE -ne 0){throw "Install failed: $($app.Package)"}
 }
 & $adb -s $serial shell pm grant org.kyf37.home android.permission.READ_EXTERNAL_STORAGE
 if($LASTEXITCODE -ne 0){throw 'Wallpaper permission grant failed'}
 & $adb -s $serial shell input keyevent 224
 & $adb -s $serial shell wm dismiss-keyguard
 & $adb -s $serial shell am start -n org.kyf37.phonesettings/.AppearanceSettings
} finally { & (Join-Path $PSScriptRoot 'phone-lock.ps1') release sky-star-icons }
