# Быстрый откат к последнему WORKING_* снапшоту
param([string]\ = 'C:\JarvisBridge')

\ = Get-ChildItem -Path 'C:\JarvisBridge\_snapshots' -Directory 
  | Where-Object { \.Name -like 'WORKING_*' } 
  | Sort-Object Name -Descending 
  | Select-Object -First 1

if (-not \) { Write-Error 'Нет доступных снапшотов WORKING_*'; exit 1 }

\ = Join-Path \.FullName 'restore_this_snapshot.ps1'
Write-Host "Using snapshot: \"
& \ -TargetRoot \
