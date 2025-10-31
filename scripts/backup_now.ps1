$src="C:\JarvisBridge"
$dest="C:\JarvisBridge\logs_backup"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$ts=Get-Date -Format "yyyyMMdd_HHmmss"
$zip=Join-Path $dest "jarvis_backup_$ts.zip"
$exclude=@(".venv","logs\archive","logs_backup","backups","_snapshots","__pycache__")
$files=Get-ChildItem -Path $src -Recurse -File | Where-Object{
    $rel=$_.FullName.Substring($src.Length).TrimStart("\")
    -not ($exclude | Where-Object { $rel -like "$_\*" })
}
if ($files.Count -gt 0) {
    Compress-Archive -Path ($files | ForEach-Object { $_.FullName }) -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "[OK] Backup создан: $zip ; файлов: $($files.Count)"
} else {
    Write-Host "[SKIP] Нет файлов для архивации."
}
