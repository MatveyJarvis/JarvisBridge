param()
$ErrorActionPreference = "Stop"

$JarvisRoot  = "C:\JarvisBridge"
$StartScript = Join-Path $JarvisRoot "start_v3_single.ps1"
$Log         = Join-Path $JarvisRoot "logs\watchdog.log"

# --- настройки анти-зависания ---
$CheckIntervalSec   = 10      # период опроса
$IdleCpuDeltaSec    = 0.20    # минимальный прирост CPU между циклами (в сек)
$IdleStrikesToKill  = 6       # сколько подряд тихих циклов считать зависанием (~1 мин)

# guard один экземпляр
$me = $PID
$others = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "powershell" -and $_.CommandLine -match "Start-JarvisWatch.ps1" -and $_.ProcessId -ne $me
}
if ($others) { Write-Output "[Watchdog] Another instance detected. Exiting."; exit }

function Write-Log([string]$msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $Log -Value "$ts`t$msg"
}

Write-Log "Watchdog started."

# состояние CPU по PID
$cpuState = @{}   # PID -> @{ cpu=<sec>; strikes=<int> }

while ($true) {
    # находим целевые процессы Jarvis
    $procsCim = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -match "jarvis_(hotword|main|visible)" -or $_.CommandLine -match "start_v3_single.ps1"
    }

    if (-not $procsCim) {
        Write-Log "Jarvis not detected. Starting..."
        Start-Process -WindowStyle Minimized -FilePath "powershell.exe" -ArgumentList @(
            "-NoProfile","-ExecutionPolicy","Bypass","-File",$StartScript
        ) | Out-Null
        Start-Sleep -Seconds 5
    } else {
        foreach ($pCim in $procsCim) {
            $p = Get-Process -Id $pCim.ProcessId -ErrorAction SilentlyContinue
            if (-not $p) { continue }
            $pid = $p.Id
            $cpuNow = $p.CPU  # суммарное CPU-время в секундах

            if (-not $cpuState.ContainsKey($pid)) {
                $cpuState[$pid] = @{ cpu = $cpuNow; strikes = 0 }
                continue
            }

            $prev = $cpuState[$pid]
            $delta = [double]($cpuNow - $prev.cpu)

            if ($delta -lt $IdleCpuDeltaSec) {
                $prev.strikes++
                if ($prev.strikes -ge $IdleStrikesToKill) {
                    Write-Log "Hang detected (PID=$pid, ΔCPU=$([math]::Round($delta,3)))  restarting..."
                    try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
                    # перезапуск сразу
                    Start-Process -WindowStyle Minimized -FilePath "powershell.exe" -ArgumentList @(
                        "-NoProfile","-ExecutionPolicy","Bypass","-File",$StartScript
                    ) | Out-Null
                    $cpuState.Remove($pid) | Out-Null
                    Start-Sleep -Seconds 5
                    continue
                }
            } else {
                # активен  сбросить счётчик
                $prev.strikes = 0
            }

            $prev.cpu = $cpuNow
            $cpuState[$pid] = $prev
        }

        # чистим состояние для завершённых PID
        $livePids = @($procsCim.ProcessId)
        foreach ($k in @($cpuState.Keys)) {
            if ($livePids -notcontains [int]$k) { $cpuState.Remove($k) | Out-Null }
        }
    }

    Start-Sleep -Seconds $CheckIntervalSec
}
