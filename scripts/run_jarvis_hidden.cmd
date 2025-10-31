@echo off
REM === Ничего не показывает на экране, т.к. запускается через .VBS (см. файл №3) ===
REM === Предполагается, что вы уже создали venv в C:\JarvisBridge\.venv ===

cd /d C:\JarvisBridge

REM Активируем виртуальное окружение
call .\.venv\Scripts\activate

REM Стартуем обёртку с приветствием и перезапуском hotword
python -X utf8 -u .\start_jarvis_with_greeting.py
