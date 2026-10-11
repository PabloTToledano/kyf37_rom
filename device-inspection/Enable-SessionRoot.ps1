# Re-enable the verified runtime root setup after a normal reboot.
# Requires the existing diagnostic/permissive flags and Interface 0 WinUSB driver.
$ErrorActionPreference = 'Stop'
$taskAdb = 'C:\Users\pablo\Downloads\platform-tools-latest-windows\platform-tools\adb.exe'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$taskProbe = Join-Path $PSScriptRoot 'probe_diag.py'
$taskRootScript = Join-Path $PSScriptRoot 'enable-app-root.sh'
& $taskAdb push $taskRootScript /data/local/tmp/enable-app-root.sh
if ($LASTEXITCODE -ne 0) { throw 'Could not copy runtime root script' }
$taskCommand = '/data/local/tmp/magisk --daemon 2>&1; chmod 711 /data/local/tmp; /data/local/tmp/magisk --sqlite "REPLACE INTO policies (uid,policy,until,logging,notification) VALUES (2000,2,0,1,1)" 2>&1; sh /data/local/tmp/enable-app-root.sh 2>&1'
& $taskPython $taskProbe --native $taskCommand
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic root activation failed' }
$taskRootResult = & $taskAdb shell 'su -c id'
if ($LASTEXITCODE -ne 0 -or $taskRootResult -notmatch 'uid=0\(root\)') {
    throw "Root verification failed: $taskRootResult"
}
Write-Output $taskRootResult
