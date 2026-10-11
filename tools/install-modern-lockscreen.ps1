$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/modern-lockscreen'))
$apk=Join-Path $folder 'SystemUI.apk'
if(-not(Test-Path -LiteralPath $apk)){throw 'Build SystemUI.apk first'}
$global:LASTEXITCODE=0
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire modern-lockscreen 15
if($LASTEXITCODE -ne 0){throw 'Phone is in use'}
try {
 $backup=Join-Path $folder 'SystemUI-before.apk'
 if(-not(Test-Path -LiteralPath $backup)) {
  $old=(& $adb -s $serial shell pm path com.android.systemui | Select-Object -First 1).Replace('package:','').Trim()
  & $adb -s $serial pull $old $backup
  if($LASTEXITCODE -ne 0){throw 'SystemUI backup failed'}
 }
 # Android 10 rejects pm updates of persistent apps. Stage an atomic system copy.
 & $adb -s $serial push (Join-Path $PSScriptRoot '../device-inspection/clear-system-temp-wp') /data/local/tmp/clear-system-temp-wp
 if($LASTEXITCODE -ne 0){throw 'Write-protection helper staging failed'}
 & $adb -s $serial push $apk /data/local/tmp/SystemUI-modern-lockscreen.apk
 if($LASTEXITCODE -ne 0){throw 'APK staging failed'}
 & $adb -s $serial shell chmod 755 /data/local/tmp/clear-system-temp-wp
 & $adb -s $serial shell '/data/local/tmp/clear-system-temp-wp --clear-system-temporary > /data/local/tmp/modern-lockscreen-system-wp.log 2>&1'
 if($LASTEXITCODE -ne 0){throw 'Cannot clear temporary system write protection'}
 & $adb -s $serial shell 'mount -o remount,rw /system'
 if($LASTEXITCODE -ne 0){throw 'System remount failed'}
 try {
  & $adb -s $serial shell 'mkdir -p /data/local/tmp/modern-lockscreen-rollback; if [ ! -f /data/local/tmp/modern-lockscreen-rollback/SystemUI.apk ]; then cp -p /system/product/priv-app/SystemUI/SystemUI.apk /data/local/tmp/modern-lockscreen-rollback/SystemUI.apk; if [ -d /system/product/priv-app/SystemUI/oat ]; then cp -rp /system/product/priv-app/SystemUI/oat /data/local/tmp/modern-lockscreen-rollback/; fi; fi'
  if($LASTEXITCODE -ne 0){throw 'System rollback staging failed'}
  & $adb -s $serial shell 'cp /data/local/tmp/SystemUI-modern-lockscreen.apk /system/product/priv-app/SystemUI/SystemUI.apk.new && chown 0:0 /system/product/priv-app/SystemUI/SystemUI.apk.new && chmod 644 /system/product/priv-app/SystemUI/SystemUI.apk.new && restorecon /system/product/priv-app/SystemUI/SystemUI.apk.new && mv /system/product/priv-app/SystemUI/SystemUI.apk.new /system/product/priv-app/SystemUI/SystemUI.apk && if [ -d /system/product/priv-app/SystemUI/oat ]; then mv /system/product/priv-app/SystemUI/oat /system/product/priv-app/SystemUI/oat-before-modern-lockscreen; fi; sync'
  if($LASTEXITCODE -ne 0){throw 'SystemUI replacement failed'}
 } finally {
  & $adb -s $serial shell 'sync; mount -o remount,ro /system'
 }
 $systemUiPid=(& $adb -s $serial shell pidof com.android.systemui).Trim()
 if($systemUiPid -match '^\d+$') { & $adb -s $serial shell kill $systemUiPid }
 Start-Sleep -Seconds 5
 & $adb -s $serial shell pidof com.android.systemui
 if($LASTEXITCODE -ne 0){throw 'SystemUI did not restart; rollback APK is in the artifact folder'}
 & $adb -s $serial shell 'sync; mount -o remount,ro /system'
 if($LASTEXITCODE -ne 0){throw 'SystemUI updated, but read-only remount needs retry after startup'}
} finally {
 & (Join-Path $PSScriptRoot 'phone-lock.ps1') release modern-lockscreen
}


