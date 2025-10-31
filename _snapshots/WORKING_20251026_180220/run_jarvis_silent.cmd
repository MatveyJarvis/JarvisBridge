@echo off
cd /d C:\JarvisBridge
rem убедимся, что папка логов есть
if not exist "C:\JarvisBridge\logs" mkdir "C:\JarvisBridge\logs"
rem стартуем скрытый VBS-обёрткой
wscript.exe //nologo "C:\JarvisBridge\run_jarvis_silent.vbs"
