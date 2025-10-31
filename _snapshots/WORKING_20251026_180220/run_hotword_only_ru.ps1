# run_hotword_only_ru.ps1
# Start Jarvis in hotword mode using jarvis_hotword.py.
# Single instance, RU forced, one mic process.

$ErrorActionPreference = "SilentlyContinue"
Write-Host "[hotword-only] Start..."

# --- Force RU & hotword for this session (no .env edits) ---
$env:JARVIS_LANG = "ru"
$env:WHISPER_LANG = "ru"
$env:WHISPER_TASK = "transcribe"
$env:TTS_LANG = "ru-RU"
$env:TTS_VOICE = "alloy"
$env:TTS_SPEED = "1.0"

$env:HOTWORD_PHRASE = "привет джарвис"
$env:WAKE_WORD = "привет джарвис"
$env:TRIGGER_PHRASE = "привет джарвис"

$env:INPUT_DEVICE_INDEX = "1"
$env:INPUT_SAMPLE_RATE = "16000"
$env:VAD_AGGRESSIVENESS = "3"
$env:MIN_SPEECH_MS = "600"
$env:CMD_MIN_MS = "600"
$env:CMD_MAX_MS = "9000"
$env:CMD_SIL_MS = "2000"
$env:HOTWORD_COOLDOWN_MS = "2000"

# --- Housekeeping: kill competing processes ---
Set-Location -Path "C:\JarvisBridge"
Write-Host "[hotword-only] Stopping competing processes..."
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
      Write-Host ("[hotword-only] Killed PID {0}" -f $pid)
    }
  } catch { }
}

Start-Sleep -Milliseconds 300

# --- Activate venv ---
Write-Host "[hotword-only] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

# --- Prevent duplicates of jarvis_hotword.py ---
Write-Host "[hotword-only] Checking duplicates..."
$already = Get-CimInstance Win32_Process |
  Where-Object { ($_.Name -match '^python(\.exe)?$') -and ($_.CommandLine -match 'jarvis_hotword\.py') }

if ($already) {
  Write-Host "[hotword-only] jarvis_hotword.py already running. Exit."
  exit 0
}

# --- Start hotword listener ---
Write-Host "[hotword-only] Starting jarvis_hotword.py ..."
python -X utf8 -u ".\jarvis_hotword.py"
