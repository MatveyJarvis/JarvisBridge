param(
    [string]\ = 'C:\JarvisBridge'
)

Write-Host '=== RESTORE THIS SNAPSHOT ==='
Write-Host 'Source snapshot: C:\JarvisBridge\_snapshots\WORKING_20251026_180220'
Write-Host ('Target root: ' + \)
Write-Host ''
\ = Read-Host 'Перезаписать файлы в C:\JarvisBridge содержимым этого снапшота? (Y/N)'
if (\ -ne 'Y' -and \ -ne 'y') { Write-Host 'Отменено.'; exit 0 }

# Останавливаем возможные процессы python в JarvisBridge (мягко)
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        if (\.Path -and \.Path -like '*JarvisBridge*') { Stop-Process -Id \.Id -Force -ErrorAction SilentlyContinue }
    } catch {}
}

# Копируем всё, КРОМЕ .venv
Get-ChildItem -Path 'C:\JarvisBridge\_snapshots\WORKING_20251026_180220' -Force | Where-Object { \.Name -ne '.venv' } | ForEach-Object {
    Copy-Item -Path \.FullName -Destination \ -Recurse -Force
}
Write-Host 'Готово: снапшот восстановлен.'
