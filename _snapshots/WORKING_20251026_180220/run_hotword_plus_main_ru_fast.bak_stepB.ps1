# run_hotword_plus_main_ru_fast.ps1 — combo-fast (visible), main(bg)+hotword(fg), ASCII-safe

$ErrorActionPreference = 'Stop'
Write-Host "[combo-fast] Start..."

# Force audio (same as v3)
$env:INPUT_DEVICE_INDEX = "1"
$env:INPUT_CHANNELS     = "1"
$env:INPUT_SAMPLE_RATE  = "16000"
$env:LANG               = "ru"
$env:VAD_AGGR           = "3"

# Kill competing processes (old hotword/main runners), keep current PS
$regex = '(jarvis_main_voice_bridge_v3\.py|jarvis_hotword\.py|run_jarvis_voice\.cmd|run_voice_bridge_v3\.cmd|start_jarvis_with_greeting\.py|run_hotword_)'
try {
    Get-CimInstance Win32_Process |
      Where-Object { $_.CommandLine -and ($_.ProcessId -ne $PID) -and ($_.CommandLine -match $regex) } |
      ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }
    Start-Sleep -Milliseconds 250
    Write-Host "[combo-fast] Competing processes: stopped."
} catch { Write-Host "[combo-fast] Cleanup warn: $($_.Exception.Message)" }

# Activate venv
$venv = 'C:\JarvisBridge\.venv\Scripts\Activate.ps1'
if (-not (Test-Path $venv)) { throw "[ERR] .venv not found: $venv" }
. $venv
Write-Host "[combo-fast] venv activated."

# Start MAIN (background, minimized)
Write-Host "[combo-fast] Starting MAIN (bg, minimized)..."
Start-Process -FilePath "python.exe" `
  -ArgumentList "-X","utf8","-u",".\jarvis_main_voice_bridge_v3.py" `
  -WorkingDirectory "C:\JarvisBridge" `
  -WindowStyle Minimized

# Start HOTWORD (foreground, visible)
Write-Host "[combo-fast] Starting HOTWORD (fg, visible)..."
Write-Host "[Hotword] Using INPUT_DEVICE_INDEX=$($env:INPUT_DEVICE_INDEX), CH=$($env:INPUT_CHANNELS), RATE=$($env:INPUT_SAMPLE_RATE)"
python -X utf8 -u .\jarvis_hotword.py
