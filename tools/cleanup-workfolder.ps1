param([switch]$Apply, [string]$PlanName='cleanup-plan-20261011.json', [string]$ReportName='cleanup-result-20261011.json')
$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
if([IO.Path]::GetFileName($PlanName) -ne $PlanName -or [IO.Path]::GetFileName($ReportName) -ne $ReportName){throw 'Plan/report must be filenames'}
$planPath=Join-Path $workspaceRoot ('device-inspection/'+$PlanName)
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if($plan.root -ne $workspaceRoot){throw 'Cleanup plan belongs to a different workspace'}
$deleted=[Collections.Generic.List[object]]::new()
$skipped=[Collections.Generic.List[object]]::new()
foreach($entry in $plan.files){
 $target=[IO.Path]::GetFullPath((Join-Path $workspaceRoot $entry.path))
 if(-not $target.StartsWith($workspaceRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Outside workspace: $target"}
 if($entry.path -match '^(\.git|phone-backup|kyf37-twrp-device)[\\/]' -or $entry.path -match 'owner-signing-key|system-stock\.img|rollback'){throw "Protected path: $target"}
 $item=Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue
 if(-not $item){continue}
 if($item.PSIsContainer){throw 'Plan must contain files only'}
 $parent=$item
 while($parent.FullName -ne $workspaceRoot){
  if($parent.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Reparse path rejected: $target"}
  $parent=Get-Item -LiteralPath (Split-Path $parent.FullName -Parent) -Force
 }
 if($item.Length -ne $entry.bytes -or ($entry.last_write_ticks -and $item.LastWriteTimeUtc.Ticks -ne $entry.last_write_ticks)){$skipped.Add(@{path=$entry.path;reason='Changed since verified plan'});continue}
 if($Apply){Remove-Item -LiteralPath $target -Force}
 $deleted.Add($entry)
}
$emptyDirectories=[Collections.Generic.List[string]]::new()
if($Apply -and $PlanName -eq 'cleanup-plan-v22.json'){
 $romRoot=[IO.Path]::GetFullPath((Join-Path $workspaceRoot 'kyf37-rom'))
 foreach($dir in Get-ChildItem -LiteralPath $romRoot -Directory){
  if($dir.Name -notmatch '^android10-go-candidate-20261007-v(\d+)$' -or [int]$Matches[1] -gt 18){continue}
  $resolved=[IO.Path]::GetFullPath($dir.FullName)
  if(-not $resolved.StartsWith($romRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or ($dir.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe retired directory'}
  if(@(Get-ChildItem -LiteralPath $resolved -Force).Count -eq 0){
   Remove-Item -LiteralPath $resolved
   $emptyDirectories.Add($resolved)
  }
 }
}
$report=@{applied=[bool]$Apply;timestamp=(Get-Date).ToString('o');files=$deleted;skipped=$skipped;bytes=($deleted | Measure-Object bytes -Sum).Sum;removed_empty_directories=$emptyDirectories}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $workspaceRoot ('device-inspection/'+$ReportName))
Write-Output ('{0} files; {1:N2} GiB; skipped {2}; applied={3}' -f $deleted.Count,($report.bytes/1GB),$skipped.Count,[bool]$Apply)
