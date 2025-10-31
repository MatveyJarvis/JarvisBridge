# start_jarvis_shell.ps1
# Открыть PS в C:\JarvisBridge, активировать .venv, подгрузить важные переменные из .env,
# задать заголовок окна и полезные алиасы.

# --- В папке проекта ---
Set-Location -Path "C:\JarvisBridge"

# --- Красивый заголовок окна ---
$Host.UI.RawUI.WindowTitle = "Jarvis Shell — C:\JarvisBridge"

# --- Активируем виртуалку, если есть ---
$venv = ".\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $venv)) {
  Write-Host "[WARN] Не найдено .venv. Запусти установку зависимостей позже." -ForegroundColor Yellow
} else {
  & $venv
}

# --- Подхватываем ключевые переменные из .env (только для текущего процесса) ---
$envPath = ".\.env"
if (Test-Path $envPath) {
  $lines = Get-Content $envPath -Encoding UTF8
  foreach ($line in $lines) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
      $name = $matches[1]
      $value = $matches[2]
      # Отобранный белый список (чтобы не засорять окружение)
      $allow = @(
        'OPENAI_API_KEY','OPENAI_STT_MODEL','OPENAI_TTS_MODEL','OPENAI_TTS_VOICE',
        'OPENAI_LLM_MODEL_STRONG','RESPONSE_LANG',
        'INPUT_DEVICE_INDEX','INPUT_SAMPLE_RATE',
        'WAKE_PHRASE','WAKE_PHRASES'
      )
      if ($allow -contains $name) {
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
      }
    }
  }
}

# --- Короткие алиасы под наши тесты ---
function sttping { python -X utf8 -u .\tests\audio\stt_ping.py }
function hotwordtest { python -X utf8 -u .\tests\hotword\hotword_cmd_stt.py }

# --- Вспомогательные подсказки ---
Write-Host ""
Write-Host "=== Jarvis Shell готов ===" -ForegroundColor Cyan
Write-Host "Проект:     C:\JarvisBridge"
Write-Host ("Python venv: " + ($(Get-Command python).Source)) -ForegroundColor DarkGray
Write-Host ("INPUT_DEVICE_INDEX=" + $env:INPUT_DEVICE_INDEX + " | SAMPLE_RATE=" + $env:INPUT_SAMPLE_RATE) -ForegroundColor DarkGray
Write-Host ""
Write-Host "Команды:" -ForegroundColor Green
Write-Host "  sttping      → быстрый тест распознавания (stt_ping.py)"
Write-Host "  hotwordtest  → пробуждение → запись команды → STT"
Write-Host ""
