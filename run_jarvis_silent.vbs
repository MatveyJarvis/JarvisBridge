' Запуск двух процессов скрыто: main + hotword. Лог в autostart.log (UTF-8)
Dim sh
Set sh = CreateObject("WScript.Shell")

' Основной мост (voice bridge)
sh.Run "cmd.exe /c chcp 65001 >NUL & set PYTHONUTF8=1 & set PYTHONIOENCODING=utf-8" _
 & " & cd /d C:\JarvisBridge" _
 & " & call .\.venv\Scripts\activate.bat" _
 & " & python -X utf8 -u .\jarvis_main_voice_bridge_v3.py >> C:\JarvisBridge\logs\autostart.log 2>&1", 0, False

' Хотворд (активация/пауза)
sh.Run "cmd.exe /c chcp 65001 >NUL & set PYTHONUTF8=1 & set PYTHONIOENCODING=utf-8" _
 & " & cd /d C:\JarvisBridge" _
 & " & call .\.venv\Scripts\activate.bat" _
 & " & python -X utf8 -u .\jarvis_hotword.py >> C:\JarvisBridge\logs\autostart.log 2>&1", 0, False
