# Cooperative lock for the single KYF37 test phone (several agents may work at once).
#   .\tools\phone-lock.ps1 acquire <your-name> [minutes]   -> waits until free, then takes the lock
#   .\tools\phone-lock.ps1 release <your-name>
#   .\tools\phone-lock.ps1 status
# Hold it only while flashing/rebooting/testing on hardware; read-only adb queries do not need it.
param([Parameter(Mandatory=$true)][string]$Action, [string]$Name = 'unknown', [int]$Minutes = 45)
$lock = Join-Path $PSScriptRoot '..\.phone.lock'
function Read-Lock { if (Test-Path $lock) { Get-Content $lock -Raw | ConvertFrom-Json } }
switch ($Action) {
  'status'  { $l = Read-Lock; if ($l -and ([datetime]$l.expires) -gt (Get-Date)) { "LOCKED by $($l.owner) until $($l.expires)" } else { 'FREE' } }
  'acquire' {
      while ($true) {
          $l = Read-Lock
          if (-not $l -or ([datetime]$l.expires) -le (Get-Date) -or $l.owner -eq $Name) { break }
          Start-Sleep 20
      }
      @{ owner = $Name; expires = (Get-Date).AddMinutes($Minutes).ToString('o') } | ConvertTo-Json | Set-Content $lock
      "acquired by $Name"
  }
  'release' { $l = Read-Lock; if (-not $l -or $l.owner -eq $Name) { Remove-Item $lock -ErrorAction SilentlyContinue; 'released' } else { "not yours: $($l.owner)" } }
}
