@echo off
setlocal ENABLEDELAYEDEXPANSION

rem === Paths ===
set "ROOT=C:\JarvisBridge"
set "ARCH=%ROOT%\z_archive_20251021"
set "ARCH_PY=%ARCH%\py"
set "ARCH_CMD=%ARCH%\cmd"
set "TESTS=%ROOT%\tests"
set "TESTS_AUDIO=%TESTS%\audio"

rem === Create folders (idempotent) ===
mkdir "%ARCH%" 2>nul
mkdir "%ARCH_PY%" 2>nul
mkdir "%ARCH_CMD%" 2>nul
mkdir "%TESTS%" 2>nul
mkdir "%TESTS_AUDIO%" 2>nul

echo [A1] Раскладываю PY-скрипты в архив...
for %%F in (
  "jarvis_main_voice_bridge.py"
  "jarvis_main_voice_bridge_v2.py"
  "jarvis_test_direct.py"
  "llm_quick_test.py"
  "mic_test.py"
  "play_one_voice.py"
  "play_probe_voices.py"
  "play_probe_voices_v2.py"
  "probe_voices.py"
  "set_openai_voice.py"
  "tts_confirm_choice.py"
  "tts_openai_preview.py"
  "tts_openai_wav.py"
  "startup_health.py"
  "hud.py"
  "dialog_logger.py"
) do (
  if exist "%ROOT%\%%~F" (
    move /Y "%ROOT%\%%~F" "%ARCH_PY%" >nul
    echo   -> moved %%~F
  )
)

echo [A1] Раскладываю CMD-скрипты в архив...
for %%F in (
  "run_jarvis_hotword_debug.cmd"
  "run_jarvis_hotword_no_pause.cmd"
  "run_jarvis_voice_bridge_debug.cmd"
  "run_jarvis_watchdog.cmd"
  "run_voice_bridge_v3_fix.cmd"
) do (
  if exist "%ROOT%\%%~F" (
    move /Y "%ROOT%\%%~F" "%ARCH_CMD%" >nul
    echo   -> moved %%~F
  )
)

echo [A1] Переношу тестовые аудиофайлы в tests\audio...
for %%F in (
  "mic_test.wav"
  "stt_test.wav"
  "tts_test.wav"
  "st_tts.wav"
  "test_record.wav"
  "tts_out.mp3"
) do (
  if exist "%ROOT%\%%~F" (
    move /Y "%ROOT%\%%~F" "%TESTS_AUDIO%" >nul
    echo   -> moved %%~F
  )
)

echo [A1] Готово. Ничего не удалялось. Все спорное в %ARCH%.
echo [A1] Проверь корень папки: должны остаться только основные файлы и ключевые CMD.
pause
endlocal
