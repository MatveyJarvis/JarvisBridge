# run_jarvis_single.ps1
# Single-instance launcher: closes competing processes, activates venv, prevents duplicates, starts the main bridge.
$ErrorActionPreference = "SilentlyContinue"

Write-Host "[single] Start..."

# 1) Project folder
Set-Location -Path "C:\JarvisBridge"

# 2) Close competing processes (python started from C:\JarvisBridge and ffmpeg)
Write-Host "[single] Stopping competing processes..."
$procs = @()

# python with command line containing C:\JarvisBridge
$procs += Get-CimInstance Win32_Process |
    Where-Object {
        ($_.Name -match '^python(\.exe)?$') -and
        ($_.CommandLine -match 'C:\\JarvisBridge')
    }

# possible leftover ffmpeg
$ffm = Get-Process -Name "ffmpeg" -ErrorAction SilentlyContinue
if ($ffm) { $procs += $ffm }

# stop unique, non-null
$procs = $procs | Where-Object { $_ -ne $null } | Select-Object -Unique
foreach ($p in $procs) {
    try {
        $pid = if ($p.ProcessId) { $p.ProcessId } else { $p.Id }
        if ($pid) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host ("[single] Killed PID {0}" -f $pid)
        }
    } catch { }
}

Start-Sleep -Milliseconds 300

# 3) Activate venv
Write-Host "[single] Activating .venv..."
& "C:\JarvisBridge\.venv\Scripts\Activate.ps1"

# 4) Prevent duplicates of main bridge
Write-Host "[single] Checking duplicates..."
$already = Get-CimInstance Win32_Process |
    Where-Object {
        ($_.Name -match '^python(\.exe)?$') -and
        ($_.CommandLine -match 'jarvis_main_voice_bridge_v3\.py')
    }

if ($already) {
    Write-Host "[single] Main bridge already running. Exit."
    exit 0
}

# 5) Start main bridge (same window to see logs)
Write-Host "[single] Starting jarvis_main_voice_bridge_v3.py ..."
python -X utf8 -u ".\jarvis_main_voice_bridge_v3.py"
