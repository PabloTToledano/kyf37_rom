param([switch]$SkipLaunch)
$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/ir-remote'))
function AdbRun { & $adb -s $serial @args; if($LASTEXITCODE -ne 0){throw "ADB operation failed: $args"} }
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire ir-remote 45
try {
 AdbRun root
 Start-Sleep 4
 $kernel=(& $adb -s $serial shell uname -v).Trim()
 if($kernel -ne '#17 SMP PREEMPT Fri Oct 9 10:04:32 CEST 2026'){throw 'Module requires the ABI-checked kernel #17; rebuild before installation'}
 foreach($file in @('kyf37_ir_tx','kyf37_ir_service','kyf37_ir_module.ko','kyf37-ir-start.sh','init.kyf37.irremote.rc')){AdbRun push (Join-Path $folder $file) /data/local/tmp/}
 AdbRun shell 'chmod 700 /data/local/tmp/kyf37_ir_tx /data/local/tmp/kyf37_ir_service /data/local/tmp/kyf37-ir-start.sh'
 AdbRun push (Join-Path $PSScriptRoot '../device-inspection/clear-system-temp-wp') /data/local/tmp/
 AdbRun shell 'chmod 700 /data/local/tmp/clear-system-temp-wp'
 AdbRun shell '/data/local/tmp/clear-system-temp-wp --clear-system-temporary'
 AdbRun shell 'mount -o remount,rw /system'
 try {
  AdbRun shell 'mkdir -p /data/local/tmp/ir-remote-rollback; for n in kyf37_ir_tx kyf37_ir_service kyf37-ir-start.sh; do if [ -f /system/bin/$n ] && [ ! -f /data/local/tmp/ir-remote-rollback/$n ]; then cp /system/bin/$n /data/local/tmp/ir-remote-rollback/$n; fi; cp /data/local/tmp/$n /system/bin/$n; chmod 755 /system/bin/$n; done'
  AdbRun shell 'cp /data/local/tmp/kyf37_ir_module.ko /system/lib/modules/kyf37_ir_module.ko; chmod 644 /system/lib/modules/kyf37_ir_module.ko; cp /data/local/tmp/init.kyf37.irremote.rc /system/etc/init/init.kyf37.irremote.rc; chmod 644 /system/etc/init/init.kyf37.irremote.rc; sync'
 }finally{AdbRun shell 'mount -o remount,ro /system'}
 AdbRun install -r (Join-Path $folder 'Kyf37Remote.apk')
 # Existing init does not parse new rc files until reboot; start this session directly.
 AdbRun shell 'for pid in $(pidof kyf37_ir_service); do kill $pid; done; /system/bin/sh /system/bin/kyf37-ir-start.sh >/data/local/tmp/kyf37-ir-service.log 2>&1 </dev/null &'
 if(-not $SkipLaunch){AdbRun shell 'am start -n org.kyf37.remote/.Remote'}
}finally{& (Join-Path $PSScriptRoot 'phone-lock.ps1') release ir-remote}
