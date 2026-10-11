# Persistent live fix; no reboot or partition writes needed.
$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
& $adb -s 981108631314 shell 'settings put global lid_behavior 1; settings put system open_sound_enabled 1; settings put system close_sound_enabled 1; dumpsys window policy | grep getLidBehavior'
if ($LASTEXITCODE -ne 0) { throw 'Unable to apply lid settings' }
