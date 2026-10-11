# Flash a KYF37 TWRP installer ZIP from Windows. Usage: .\tools\flash-release.ps1 kyf37-rom\kyf37-android10-go-20261007-twrp-v14.zip
# Sequence proven on 2026-10-08: request recovery via misc -> push -> twrp install -> clear misc -> reboot -> wait.
# Needs: phone running Android with USB debugging (root adb), or already in TWRP. SD card in the phone with >= 2.5 GB free.
param([Parameter(Mandatory=$true)][string]$Zip, [switch]$UseExistingSdZip)
$ErrorActionPreference = 'Stop'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$s = '981108631314'
$name = Split-Path $Zip -Leaf
$expected = (Get-Content "$Zip.sha256").Split(' ')[0]

function Wait-State($state, $seconds) {
    $t = Get-Date
    while (((Get-Date) - $t).TotalSeconds -lt $seconds) {
        Start-Sleep 4
        if ((& $adb devices | Select-String $s) -match $state) { return $true }
    }
    return $false
}

$state = (& $adb devices | Select-String $s)
if ($state -notmatch 'recovery') {
    & $adb -s $s root | Out-Null; Start-Sleep 4
    # Android's own "reboot recovery" does not write the BCB on this ROM: write the misc request ourselves.
    & $adb -s $s shell 'printf "boot-recovery\000" | dd of=/dev/block/bootdevice/by-name/misc bs=1 count=14 conv=notrunc 2>/dev/null; printf "recovery\n" | dd of=/dev/block/bootdevice/by-name/misc bs=1 seek=64 count=9 conv=notrunc 2>/dev/null; sync; reboot'
    if (-not (Wait-State 'recovery' 240)) { throw 'Phone did not reach TWRP' }
    Start-Sleep 8
}
if (-not $UseExistingSdZip) {
    & $adb -s $s push $Zip /external_sd/ | Select-Object -Last 1
}
$actual = (& $adb -s $s shell "sha256sum /external_sd/$name").Split(' ')[0]
if ($actual -ne $expected) { throw "SHA mismatch: $actual vs $expected" }
$installOutput = & $adb -s $s shell "twrp set tw_signed_zip_verify 0 >/dev/null 2>&1; twrp install /external_sd/$name"
$installExit = $LASTEXITCODE
$installOutput
if ($installExit -ne 0 -or ($installOutput -join "`n") -notmatch 'Successful|Install.*complete|installation.*succeeded') {
    throw 'Installation success was not confirmed; leaving the phone in TWRP for inspection.'
}
# Always clear the recovery request so the next boot is Android.
& $adb -s $s shell 'dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=80 conv=notrunc 2>/dev/null; sync'
& $adb -s $s reboot
Start-Sleep 30
$t = Get-Date
while (((Get-Date) - $t).TotalSeconds -lt 600) {
    Start-Sleep 8
    if ((& $adb -s $s shell 'getprop sys.boot_completed' 2>$null) -match '1') { "boot_completed after $([int]((Get-Date)-$t).TotalSeconds)s"; exit 0 }
}
throw 'Android did not finish booting; see AGENTS.md section 4 (loop recovery).'
