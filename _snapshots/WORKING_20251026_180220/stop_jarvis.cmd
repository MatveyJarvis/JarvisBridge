@echo off
REM Останавливаем процессы main и hotword БЕЗ PAUSE
powershell -NoLogo -NoProfile -Command ^
  "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'jarvis_main_voice_bridge_v3\.py|jarvis_hotword\.py' }; if($p){$p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }}"

echo [OK] Jarvis остановлен (если был запущен).
