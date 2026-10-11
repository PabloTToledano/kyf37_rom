param([string]$Name='brightness')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$file=Join-Path $root 'kyf37-rom/brightness/lights.kyf37.so'
function AdbRun([string[]]$Arguments) {
    & $adb -s 981108631314 @Arguments
    if($LASTEXITCODE -ne 0){throw "ADB failed: $Arguments"}
}
if(-not(Test-Path -LiteralPath $file)){throw "Missing $file"}
& "$PSScriptRoot/phone-lock.ps1" acquire $Name 15
try {
    AdbRun @('shell','test "$(id -u)" = 0')
    AdbRun @('push',$file,'/data/local/tmp/lights.kyf37.so')
    AdbRun @('push',(Join-Path $root 'device-inspection/clear-system-temp-wp'),'/data/local/tmp/clear-system-temp-wp')
    AdbRun @('shell','chmod 755 /data/local/tmp/clear-system-temp-wp; /data/local/tmp/clear-system-temp-wp --clear-system-temporary')
    AdbRun @('shell','set -e; mkdir -p /data/local/tmp/brightness-rollback; if [ -f /vendor/lib/hw/lights.kyf37.so ]; then if [ ! -f /data/local/tmp/brightness-rollback/lights.kyf37.so ]; then cp /vendor/lib/hw/lights.kyf37.so /data/local/tmp/brightness-rollback/; fi; else touch /data/local/tmp/brightness-rollback/originally-absent; fi; mount -o remount,rw /system')
    try {
        AdbRun @('shell','set -e; cp /data/local/tmp/lights.kyf37.so /vendor/lib/hw/lights.kyf37.so; chown root:root /vendor/lib/hw/lights.kyf37.so; chmod 644 /vendor/lib/hw/lights.kyf37.so; restorecon /vendor/lib/hw/lights.kyf37.so; sync')
    } finally { AdbRun @('shell','mount -o remount,ro /system') }
    AdbRun @('shell','setprop ctl.restart vendor.light-hal-2-0')
    Start-Sleep -Seconds 3
    AdbRun @('shell','sha256sum /vendor/lib/hw/lights.kyf37.so; getprop init.svc.vendor.light-hal-2-0')
} finally { & "$PSScriptRoot/phone-lock.ps1" release $Name }
