# One-command "reboot into recovery" for the KYF37. `adb reboot recovery` does NOT work on this phone: the bootloader only
# enters recovery when misc holds a boot-recovery request. This writes the verified 1536-byte request (first 1088 bytes are
# the BCB; the rest preserves the live bytes) from Android with root, reads it back, and reboots.
# Requires: phone booted in Android, adb authorized, root via `adb root` (userdebug) or Magisk su.
# Usage:  .\tools\enter-twrp.ps1          (hold tools/phone-lock.ps1 yourself if other agents use the phone)
# If Android does not boot / adb is unreachable use the USB download-mode procedure instead (KYF37-USB-RECOVERY-RUNBOOK.md).
param([int]$WaitSeconds = 120)
$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$req = Join-Path $PSScriptRoot 'misc-recovery-request.bin'
if (-not (Test-Path $req)) { throw "missing $req" }
$state = (& $adb get-state 2>$null)
if ($state -eq 'recovery') { Write-Host 'already in recovery'; exit 0 }
if ($state -ne 'device') { throw "phone not reachable over adb (state='$state')" }
& $adb push $req /data/local/tmp/misc-request.bin | Out-Null
& $adb root | Out-Null
Start-Sleep -Seconds 3
$out = & $adb shell "dd if=/data/local/tmp/misc-request.bin of=/dev/block/bootdevice/by-name/misc bs=512 count=3 conv=notrunc 2>&1; sync; dd if=/dev/block/bootdevice/by-name/misc bs=512 count=3 2>/dev/null > /data/local/tmp/misc-readback.bin; cmp /data/local/tmp/misc-request.bin /data/local/tmp/misc-readback.bin && echo MISC_VERIFIED"
Write-Host $out
if ($out -notmatch 'MISC_VERIFIED') { throw 'misc readback did not match; NOT rebooting' }
& $adb reboot | Out-Null
$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    $s = (& $adb get-state 2>$null)
    if ($s -eq 'recovery') { Write-Host 'IN_RECOVERY'; exit 0 }
}
throw "phone did not appear in recovery within $WaitSeconds s (check the screen / use download mode)"
