param()
$ErrorActionPreference = "Stop"
$JarvisRoot  = "C:\JarvisBridge"
$StartScript = Join-Path $JarvisRoot "start_v3_single.ps1"
$Log         = Join-Path $JarvisRoot "logs\watchdog.log"
$CheckIntervalSec = 10
$IdleCpuDeltaSec = 0.2
$IdleStrikesToKill = 6
function Write-Log($msg){$ts=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss");Add-Content -Path $Log -Value "$ts`t$msg"}
Write-Log "Watchdog started."

$cpuState=@{}

while ($true){
    $procs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*JarvisBridge*" }
    if(-not $procs){
        Write-Log "Jarvis not detected. Starting..."
        Start-Process -WindowStyle Minimized -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$StartScript) | Out-Null
        Start-Sleep -Seconds 5
    } else {
        foreach($p in $procs){
            $pid=$p.Id; $cpuNow=$p.CPU
            if(-not $cpuState.ContainsKey($pid)){$cpuState[$pid]=@{cpu=$cpuNow;strikes=0};continue}
            $prev=$cpuState[$pid];$delta=[double]($cpuNow-$prev.cpu)
            if($delta -lt $IdleCpuDeltaSec){
                $prev.strikes++
                if($prev.strikes -ge $IdleStrikesToKill){
                    Write-Log "Hang detected (PID=$pid, ΔCPU=$([math]::Round($delta,3)))  restarting..."
                    try{Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue}catch{}
                    Start-Process -WindowStyle Minimized -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$StartScript) | Out-Null
                    $cpuState.Remove($pid)|Out-Null
                    Start-Sleep -Seconds 5
                    continue
                }
            } else {$prev.strikes=0}
            $prev.cpu=$cpuNow;$cpuState[$pid]=$prev
        }
        $live=@($procs.Id)
        foreach($k in @($cpuState.Keys)){if($live -notcontains [int]$k){$cpuState.Remove($k)|Out-Null}}
    }
    Start-Sleep -Seconds $CheckIntervalSec
}
