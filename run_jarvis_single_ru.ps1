# run_jarvis_single_ru.ps1
# Single-instance launcher with forced RU language for STT/TTS.
$ErrorActionPreference = "SilentlyContinue"

Write-Host "[single:ru] Start..."

# 0) Force RU-related env vars for this session (do not touch .env)
$env:JARVIS_LANG = "ru"
$env:WHISPER_LANG = "ru"
$env:WHISPER_TASK = "transcribe"
$env:TTS_LANG = "ru-RU"
$env:TTS_VOICE = "alloy"
$env:TTS_SPEED = "1.0"
$env:REQUIRE_ACTIVATION_AFTER_STOP = "false"

# 1) Project folder
Set-Location -Path "C:\JarvisBridge"

# 2) Close competing processes (python from C:\JarvisBridge and ffmpeg)
Write-Host "[single:ru] Stopping competing processes..."
$procs = @()

$procs += Get-CimInstance Win32_Process |
  Where-Object {
    ($_.Name -match '^python(\.exe)?$') -and
    ($_.CommandLine -match 'C:\\JarvisBridge')
  }

$ffm = Get-Process -Name "ffmpeg" -ErrorAction SilentlyContinue
if ($ffm) { $procs += $ffm }

$procs = $procs | Where-Object { $_ -ne $null } | Select-Object -Unique
foreach ($p in $procs) {
  try {
    $pid = if ($p.ProcessId) { $p.ProcessId } else { $p.Id }
    if ($pid) {
      Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
      Write-Host ("[single:ru] Killed PID {0}" -f $pid)
    }
  } catch { }
}

Start-Sleep -Milliseconds 300

# 3) Activate venv
Write-Host "[single:ru] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

# 4) Prevent duplicates of main bridge
Write-Host "[single:ru] Checking duplicates..."
$already = Get-CimInstance Win32_Process |
  Where-Object {
    ($_.Name -match '^python(\.exe)?$') -and
    ($_.CommandLine -match 'jarvis_main_voice_bridge_v3\.py')
  }

if ($already) {
  Write-Host "[single:ru] Main bridge already running. Exit."
  exit 0
}

# 5) Start main bridge (same window to see logs)
Write-Host "[single:ru] Starting jarvis_main_voice_bridge_v3.py ..."
python -X utf8 -u ".\jarvis_main_voice_bridge_v3.py"
