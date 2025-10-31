# run_jarvis_hotword_ru.ps1
# Force RU, hotword mode, and input device index. Single-instance safe launcher.
$ErrorActionPreference = "SilentlyContinue"

Write-Host "[hotword:ru] Start..."

# --- Force config for this session (no .env edits) ---
$env:JARVIS_LANG = "ru"
$env:WHISPER_LANG = "ru"
$env:WHISPER_TASK = "transcribe"
$env:TTS_LANG = "ru-RU"
$env:TTS_VOICE = "alloy"
$env:TTS_SPEED = "1.0"

# hotword mode & phrase
$env:START_MODE = "hotword"             # instead of 'activation'
$env:HOTWORD_PHRASE = "привет джарвис"  # lower-case ru phrase

# mic & VAD
$env:INPUT_DEVICE_INDEX = "1"           # if нужно будет — поменяем на 0/2
$env:INPUT_SAMPLE_RATE = "16000"
$env:VAD_AGGRESSIVENESS = "3"
$env:MIN_SPEECH_MS = "600"
$env:CMD_MIN_MS = "600"
$env:CMD_MAX_MS = "9000"
$env:CMD_SIL_MS = "2000"
$env:HOTWORD_COOLDOWN_MS = "2000"

# after stop: no extra 'activation' required
$env:REQUIRE_ACTIVATION_AFTER_STOP = "false"

# --- Single-instance housekeeping ---
Set-Location -Path "C:\JarvisBridge"
Write-Host "[hotword:ru] Stopping competing processes..."
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
      Write-Host ("[hotword:ru] Killed PID {0}" -f $pid)
    }
  } catch { }
}

Start-Sleep -Milliseconds 300

Write-Host "[hotword:ru] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

Write-Host "[hotword:ru] Checking duplicates..."
$already = Get-CimInstance Win32_Process |
  Where-Object { ($_.Name -match '^python(\.exe)?$') -and ($_.CommandLine -match 'jarvis_main_voice_bridge_v3\.py') }

if ($already) {
  Write-Host "[hotword:ru] Main bridge already running. Exit."
  exit 0
}

Write-Host "[hotword:ru] Starting jarvis_main_voice_bridge_v3.py ..."
python -X utf8 -u ".\jarvis_main_voice_bridge_v3.py"
