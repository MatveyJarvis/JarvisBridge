# run_hotword_plus_main_ru.ps1
# Starts BOTH: main bridge (in a minimized background console) + hotword listener (foreground).
# RU language forced for this session. Designed for quick end-to-end check.

$ErrorActionPreference = "SilentlyContinue"
Write-Host "[combo] Start..."

# --- Force RU & common flags (session only, no .env edits) ---
$env:JARVIS_LANG = "ru"
$env:WHISPER_LANG = "ru"
$env:WHISPER_TASK = "transcribe"
$env:TTS_LANG = "ru-RU"
$env:TTS_VOICE = "alloy"
$env:TTS_SPEED = "1.0"

# After stop: no extra activation phrase
$env:REQUIRE_ACTIVATION_AFTER_STOP = "false"

# Hotword phrase + input/VAD
$env:HOTWORD_PHRASE = "привет джарвис"
$env:INPUT_DEVICE_INDEX = "1"
$env:INPUT_SAMPLE_RATE = "16000"
$env:VAD_AGGRESSIVENESS = "3"
$env:MIN_SPEECH_MS = "600"
$env:CMD_MIN_MS = "600"
$env:CMD_MAX_MS = "9000"
$env:CMD_SIL_MS = "2000"
$env:HOTWORD_COOLDOWN_MS = "2000"

# --- Housekeeping: kill old python/ffmpeg from our folder ---
Set-Location -Path "C:\JarvisBridge"
Write-Host "[combo] Stopping competing processes..."
$procs = @()

$procs += Get-CimInstance Win32_Process |
  Where-Object { ($_.Name -match '^python(\.exe)?$') -and ($_.CommandLine -match 'C:\\JarvisBridge') }

$ffm = Get-Process -Name "ffmpeg" -ErrorAction SilentlyContinue
if ($ffm) { $procs += $ffm }

$procs = $procs | Where-Object { $_ -ne $null } | Select-Object -Unique
foreach ($p in $procs) {
  try {
    $pid = if ($p.ProcessId) { $p.ProcessId } else { $p.Id }
    if ($pid) {
      Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
      Write-Host ("[combo] Killed PID {0}" -f $pid)
    }
  } catch { }
}

Start-Sleep -Milliseconds 300

# --- Activate venv ---
Write-Host "[combo] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

# --- Start MAIN bridge in a separate minimized console (background) ---
Write-Host "[combo] Starting MAIN bridge in background..."
$mainArgs = '-NoProfile -ExecutionPolicy Bypass -Command "cd C:\JarvisBridge; python -X utf8 -u .\jarvis_main_voice_bridge_v3.py"'
Start-Process -FilePath "powershell.exe" -ArgumentList $mainArgs -WindowStyle Minimized

# Small delay to let main initialize
Start-Sleep -Seconds 2

# --- Start HOTWORD in this window (so you see triggers) ---
Write-Host "[combo] Starting HOTWORD listener (foreground)..."
python -X utf8 -u ".\jarvis_hotword.py"
