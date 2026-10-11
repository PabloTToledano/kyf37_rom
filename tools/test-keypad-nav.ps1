# On-device checks for the keypad-navigation build (KEYPAD-NAV.md). Needs the framework from the
# focus-theme build to be FLASHED (View hook, ViewRootImpl stage and Kyf37FocusTheme are framework code).
# Hold the phone lock first:  .\tools\phone-lock.ps1 acquire <name> 30
# Usage: .\tools\test-keypad-nav.ps1 [-OutDir kyf37-rom\keypad-nav\shots]
param([string]$OutDir = "$PSScriptRoot\..\kyf37-rom\keypad-nav\shots")
$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
New-Item -ItemType Directory -Force $OutDir | Out-Null
function sh($c) { & $adb shell $c }
function shot($n) { sh "screencap -p /sdcard/$n.png" | Out-Null; & $adb pull "/sdcard/$n.png" "$OutDir\$n.png" | Out-Null; sh "rm /sdcard/$n.png" | Out-Null }

# 0. framework present?
$has = sh "ls /system/framework/framework.jar >/dev/null 2>&1; dumpsys package org.kyf37.phonesettings | grep -c versionName"
"phone settings installed: $has"

# 1. palettes: open the Appearance page, cycle every theme live, screenshot (no reboot)
sh 'am start -n org.kyf37.phonesettings/.AppearanceSettings' | Out-Null; Start-Sleep 2
foreach ($i in 0..6) {
    sh "settings put global kyf37_focus_theme $i"; Start-Sleep 1
    sh 'input keyevent KEYCODE_DPAD_DOWN'; Start-Sleep -Milliseconds 500
    shot "focus-theme-$i"
}
sh 'settings put global kyf37_focus_theme 0'

# 2. Clear/Back -> backspace. Uses the debug override because adb input has scan code 0.
sh 'setprop debug.kyf37.back_del_any true'
sh 'am start -a android.intent.action.INSERT -t vnd.android.cursor.dir/raw_contact -e name abc' | Out-Null; Start-Sleep 3
shot 'backdel-before'
sh 'input keyevent KEYCODE_BACK'; Start-Sleep 1     # -> deletes "c" when the name field has focus
shot 'backdel-after-1'
"If the contact editor is still open and the name shows 'ab', rule works. Repeat until empty: the NEXT Back must leave the screen."
sh 'setprop debug.kyf37.back_del_any false'

# 3. pointer: F3 toggles the redesigned cursor
sh 'input keyevent KEYCODE_F3'; Start-Sleep 1; shot 'pointer-on'
sh 'input keyevent KEYCODE_F3'
"done; screenshots in $OutDir"
