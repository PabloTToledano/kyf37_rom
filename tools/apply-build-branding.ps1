$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$workspace=Split-Path $PSScriptRoot -Parent
$folder=Join-Path $workspace 'kyf37-rom/build-branding'
New-Item -ItemType Directory -Force $folder | Out-Null
function Adb([string[]]$Arguments) {
    & $adb -s $serial @Arguments
    if ($LASTEXITCODE -ne 0) { throw "ADB failed: $($Arguments[0])" }
}
& "$PSScriptRoot/phone-lock.ps1" acquire build-branding 10
try {
    $backup=Join-Path $folder 'build.prop-before'
    if (-not (Test-Path $backup)) { Adb @('pull','/system/build.prop',$backup) }
    $current=Join-Path $folder 'build.prop-current'
    Adb @('pull','/system/build.prop',$current)
    $lines=[IO.File]::ReadAllLines($current)
    $found=$false
    for($i=0;$i -lt $lines.Length;$i++) {
        if($lines[$i].StartsWith('ro.build.display.id=')) {
            $display=$lines[$i].Substring(20).Replace('pablo','althia').Replace(' test-keys','')
            $lines[$i]='ro.build.display.id='+$display
            $found=$true
        }
    }
    if (-not $found) { throw 'Build display property missing' }
    $utf8=New-Object System.Text.UTF8Encoding($false)
    $patched=Join-Path $folder 'build.prop'
    $override=Join-Path $folder 'display.properties'
    [IO.File]::WriteAllText($patched,($lines -join "`n")+"`n",$utf8)
    [IO.File]::WriteAllText($override,"ro.build.display.id=$display`n",$utf8)
    Adb @('push',$patched,'/data/local/tmp/kyf37-branded-build.prop')
    Adb @('push',$override,'/data/local/tmp/kyf37-display.properties')
    Adb @('push',(Join-Path $workspace 'device-inspection/clear-system-temp-wp'),'/data/local/tmp/clear-system-temp-wp')
    Adb @('shell','chmod 755 /data/local/tmp/clear-system-temp-wp; /data/local/tmp/clear-system-temp-wp --clear-system-temporary')
    Adb @('shell','mount -o remount,rw /system')
    try {
        Adb @('shell','cp /data/local/tmp/kyf37-branded-build.prop /system/build.prop && chown 0:0 /system/build.prop && chmod 644 /system/build.prop && restorecon /system/build.prop && sync')
    } finally { Adb @('shell','mount -o remount,ro /system') }
    Adb @('shell','/system/xbin/magisk resetprop --file /data/local/tmp/kyf37-display.properties')
    Adb @('shell','getprop ro.build.display.id; sha256sum /system/build.prop; mount | grep " /system "')
} finally { & "$PSScriptRoot/phone-lock.ps1" release build-branding }
