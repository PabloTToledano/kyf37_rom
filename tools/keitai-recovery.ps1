# Safe test plan for the keitai recovery. DRY RUN unless -Execute is given. The LEAD runs this with the owner present.
#
#   .\tools\keitai-recovery.ps1 -Action bootslot-install  [-Execute]   (1) Android -> writes keitai recovery into the BOOT partition
#   .\tools\keitai-recovery.ps1 -Action bootslot-restore  [-Execute]   (2) from the running keitai recovery (or TWRP): puts the saved Android boot back
#   .\tools\keitai-recovery.ps1 -Action recovery-install  [-Execute]   (3) ONLY after (1) passed: writes it into RECOVERY (backs up the old TWRP first)
#   .\tools\keitai-recovery.ps1 -Action recovery-rollback [-Execute]   (4) one command: restores the previous TWRP into RECOVERY
#
# Only the boot and recovery partitions are ever written (whitelist in keitai-write-partition.sh), every write is hash gated
# and read back. misc is touched only in bootslot-* (first 32 bytes zeroed, the documented way to clear a recovery request).
param([Parameter(Mandatory=$true)][ValidateSet('bootslot-install','bootslot-restore','recovery-install','recovery-rollback')][string]$Action,
      [switch]$Execute, [string]$LockName = 'keitai-recovery')
$ErrorActionPreference = 'Stop'
$env:MSYS_NO_PATHCONV = '1'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$root = Split-Path $PSScriptRoot -Parent
$kd = Join-Path $root 'kyf37-twrp-device\keitai'
$bk = Join-Path $root 'phone-backup\keitai-test'
$helper = Join-Path $root 'device-inspection\keitai-write-partition.sh'
$wp = Join-Path $root 'device-inspection\clear-recovery-boot-temp-wp'
$imgRec = Join-Path $kd 'kyf37-keitai-recovery-dispfix-owner-signed.img'
$imgBoot = Join-Path $kd 'kyf37-keitai-recovery-BOOTSLOT-dispfix-owner-signed.img'
$oldTwrp = Join-Path $root 'kyf37-twrp-device\kyf37-twrp-owner-signed.img'
$oldTwrpMd5 = '7c564a1e8bac242b14d99a7f2f9b0c5c'   # README: installed TWRP 3.7.0_9-0
function Md5($f) { (Get-FileHash $f -Algorithm MD5).Hash.ToLower() }
function Sh($cmd) { (& $adb -s 981108631314 shell $cmd) -join "`n" }
function Step($t) { Write-Host "==> $t" -ForegroundColor Cyan }
function Do-Or-Say($t, [scriptblock]$b) { if ($Execute) { & $b } else { Write-Host "[dry-run] $t" -ForegroundColor Yellow } }

New-Item -ItemType Directory -Force $bk | Out-Null
foreach ($f in @($imgRec, $imgBoot, $helper, $wp)) { if (-not (Test-Path $f)) { throw "missing $f" } }
& python (Join-Path $root 'device-inspection\verify-keitai-image.py') $imgRec | Select-String 'RESULT' | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { throw 'Recovery image verification failed' }
& python (Join-Path $root 'device-inspection\verify-keitai-image.py') --boot $imgBoot | Select-String 'RESULT' | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { throw 'Boot-slot image verification failed' }
if (-not $Execute) {
  Write-Host "[dry-run] action '$Action': would back up the partition, push images + helper, write with hash gates and readback, clear misc where noted. Re-run with -Execute." -ForegroundColor Yellow
  Write-Host "images: $imgRec`n        $imgBoot"
  exit 0
}
$state = (& $adb -s 981108631314 get-state 2>$null)
Step "adb state: $state   serial: $((& $adb -s 981108631314 get-serialno))"
if ($state -ne 'device' -and $state -ne 'recovery') { throw "phone not reachable (state '$state'). See RECOVERY-KEITAI.md section 'If it does not come up'." }
$model = (& $adb -s 981108631314 shell 'getprop ro.product.model' 2>$null) -join ''
if ($state -eq 'device') { & $adb -s 981108631314 root | Out-Null; Start-Sleep 3 }
if ((Sh 'id -u').Trim() -ne '0') { throw 'adb shell is not root' }

if ($Execute) { & (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire $LockName 30 }
try {
  & $adb -s 981108631314 push $helper /data/local/tmp/keitai-write-partition.sh | Out-Null
  & $adb -s 981108631314 push $wp /data/local/tmp/clear-recovery-boot-temp-wp | Out-Null
  Sh 'chmod 755 /data/local/tmp/keitai-write-partition.sh /data/local/tmp/clear-recovery-boot-temp-wp' | Out-Null
  $partitionRoot = '/dev/block/bootdevice/by-name'

  function Backup-Partition($part, $outName) {
      Step "backing up $part"
      Sh "dd if=$partitionRoot/$part of=/data/local/tmp/$outName bs=4096 2>/dev/null; sync" | Out-Null
      $dev = (Sh "md5sum /data/local/tmp/$outName").Split(' ')[0]
      $dest = Join-Path $bk $outName
      & $adb -s 981108631314 pull "/data/local/tmp/$outName" $dest | Out-Null
      if ((Md5 $dest) -ne $dev) { throw "laptop copy of $part backup does not match device hash" }
      if ((Get-Item $dest).Length -ne 16777216) { throw "$part backup has wrong size" }
      $sd = (Sh 'ls -d /storage/*-* /external_sd 2>/dev/null | head -1').Trim()
      if ($sd) { Sh "cp /data/local/tmp/$outName $sd/$outName; sync" | Out-Null; Write-Host "also copied to SD ($sd)" }
      else { Write-Host 'no SD card found: backup is on the laptop and in /data/local/tmp only' -ForegroundColor Yellow }
      Write-Host "$part backup md5 $dev -> $dest"
      return $dev
  }
  function Write-Part($part, $img, $curMd5) {
      $m = Md5 $img
      & $adb -s 981108631314 push $img /data/local/tmp/write.img | Out-Null
      $r = Sh "sh /data/local/tmp/keitai-write-partition.sh $part /data/local/tmp/write.img $m $curMd5"
      Write-Host $r
      if ($r -notmatch 'KEITAI_WRITE_VERIFIED') { throw "write of $part FAILED verification: $r" }
  }
  function Clear-Misc { Sh 'dd if=/dev/zero of=/dev/block/bootdevice/by-name/misc bs=1 count=32 conv=notrunc 2>/dev/null; sync; dd if=/dev/block/bootdevice/by-name/misc bs=1 count=32 2>/dev/null | od -An -tx1 | head -2' }

  switch ($Action) {
    'bootslot-install' {
      if ($state -ne 'device') { throw 'bootslot-install must start from running Android' }
      Do-Or-Say "back up boot, write keitai (BOOT-signed) image to boot, clear misc, reboot" {
        $cur = Backup-Partition 'boot' 'boot-android-backup.img'
        Write-Part 'boot' $imgBoot $cur
        Step 'clearing misc request (first 32 bytes)'; Write-Host (Clear-Misc)
        Write-Host "Backup md5 for the restore: $cur" -ForegroundColor Green
        Set-Content (Join-Path $bk 'boot-android-backup.md5') $cur
        Write-Host 'Rebooting. The phone should show the KEITAI recovery menu (not Android). adb should list state "recovery".'
        & $adb -s 981108631314 reboot | Out-Null
        $t = (Get-Date).AddSeconds(150)
        while ((Get-Date) -lt $t) { Start-Sleep 5; $s = (& $adb -s 981108631314 get-state 2>$null); if ($s -eq 'recovery') { Write-Host 'ADB_UP_IN_RECOVERY' -ForegroundColor Green; break } }
        Write-Host 'Now test the UI by hand (RECOVERY-KEITAI.md checklist), then run -Action bootslot-restore.'
      }
    }
    'bootslot-restore' {
      Do-Or-Say "write phone-backup/keitai-test/boot-android-backup.img back to boot, verify, clear misc, reboot to Android" {
        $f = Join-Path $bk 'boot-android-backup.img'
        if (-not (Test-Path $f)) { throw "no backup at $f" }
        $want = (Get-Content (Join-Path $bk 'boot-android-backup.md5')).Trim()
        if ((Md5 $f) -ne $want) { throw 'backup file hash changed since it was taken' }
        # current boot must be the keitai image we wrote (or already the backup)
        Write-Part 'boot' $f '-'
        Step 'clearing misc'; Write-Host (Clear-Misc)
        & $adb -s 981108631314 reboot | Out-Null
        Write-Host 'Rebooting into Android (first boot takes minutes).'
      }
    }
    'recovery-install' {
      Do-Or-Say "back up recovery (must equal the known TWRP md5 $oldTwrpMd5), write keitai recovery, verify" {
        if ((Test-Path (Join-Path $bk 'bootslot-passed.flag')) -eq $false) { throw 'create phone-backup\keitai-test\bootslot-passed.flag after the boot-slot test passed' }
        $cur = Backup-Partition 'recovery' 'recovery-twrp-backup.img'
        if ($cur -ne $oldTwrpMd5) { Write-Host "NOTE: recovery md5 $cur differs from README md5 (an updated TWRP?) - the backup is what rollback restores" -ForegroundColor Yellow }
        try { Write-Part 'recovery' $imgRec $cur }
        catch { Write-Host 'write failed: restoring previous recovery' -ForegroundColor Red; Write-Part 'recovery' (Join-Path $bk 'recovery-twrp-backup.img') '-'; throw }
        Set-Content (Join-Path $bk 'recovery-twrp-backup.md5') $cur
        Write-Host 'recovery now holds the keitai image. Test: .\tools\enter-twrp.ps1'
      }
    }
    'recovery-rollback' {
      Do-Or-Say "write phone-backup/keitai-test/recovery-twrp-backup.img (or the shipped kyf37-twrp-owner-signed.img) back to recovery" {
        $f = Join-Path $bk 'recovery-twrp-backup.img'
        if (-not (Test-Path $f)) { $f = $oldTwrp; Write-Host 'using shipped owner-signed TWRP image' }
        Write-Part 'recovery' $f '-'
      }
    }
  }
} finally {
  if ($Execute) { & (Join-Path $PSScriptRoot 'phone-lock.ps1') release $LockName }
}
