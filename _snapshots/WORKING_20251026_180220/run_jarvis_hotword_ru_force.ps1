# run_jarvis_hotword_ru_force.ps1
# Force hotword mode + RU for STT/TTS. Covers multiple env names and also passes CLI hints.
$ErrorActionPreference = "SilentlyContinue"

Write-Host "[hotword:force] Start..."

# --- Hard RU language (session only) ---
$env:JARVIS_LANG = "ru"
$env:WHISPER_LANG = "ru"
$env:WHISPER_TASK = "transcribe"
$env:TTS_LANG = "ru-RU"
$env:TTS_VOICE = "alloy"
$env:TTS_SPEED = "1.0"

# --- Force HOTWORD mode (set many common names) ---
$env:START_MODE = "hotword"
$env:STARTUP_MODE = "hotword"
$env:JARVIS_START_MODE = "hotword"
$env:MODE = "hotword"

# Hotword phrase (common names)
$env:HOTWORD_PHRASE = "привет джарвис"
$env:WAKE_WORD = "привет джарвис"
$env:TRIGGER_PHRASE = "привет джарвис"

# After stop: no extra activation
$env:REQUIRE_ACTIVATION_AFTER_STOP = "false"

# Mic & VAD (adjustable later)
$env:INPUT_DEVICE_INDEX = "1"
$env:INPUT_SAMPLE_RATE = "16000"
$env:VAD_AGGRESSIVENESS = "3"
$env:MIN_SPEECH_MS = "600"
$env:CMD_MIN_MS = "600"
$env:CMD_MAX_MS = "9000"
$env:CMD_SIL_MS = "2000"
$env:HOTWORD_COOLDOWN_MS = "2000"

# --- Single-instance housekeeping ---
Set-Location -Path "C:\JarvisBridge"
Write-Host "[hotword:force] Stopping competing processes..."
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
      Write-Host ("[hotword:force] Killed PID {0}" -f $pid)
    }
  } catch { }
}

Start-Sleep -Milliseconds 300

Write-Host "[hotword:force] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

Write-Host "[hotword:force] Checking duplicates..."
$already = Get-CimInstance Win32_Process |
  Where-Object { ($_.Name -match '^python(\.exe)?$') -and ($_.CommandLine -match 'jarvis_main_voice_bridge_v3\.py') }

if ($already) {
  Write-Host "[hotword:force] Main bridge already running. Exit."
  exit 0
}

# --- Start main bridge with CLI hints (safe if unknown) ---
Write-Host "[hotword:force] Starting jarvis_main_voice_bridge_v3.py ..."
python -X utf8 -u ".\jarvis_main_voice_bridge_v3.py" `
  --mode hotword `
  --start-mode hotword `
  --hotword "привет джарвис" `
  --lang ru `
  --input-device 1
