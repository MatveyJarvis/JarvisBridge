param()
$ErrorActionPreference = "Stop"
$JarvisRoot  = "C:\JarvisBridge"
$StartScript = Join-Path $JarvisRoot "start_v3_single.ps1"
$Log         = Join-Path $JarvisRoot "logs\watchdog.log"

function Write-Log($msg){$ts=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss");Add-Content -Path $Log -Value "$ts`t$msg"}
Write-Log "=== Watchdog manual session started ==="

while ($true){
    $procs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*JarvisBridge*" }
    if (-not $procs){
        Write-Log "Jarvis not detected  starting..."
        Start-Process -WindowStyle Minimized -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$StartScript) | Out-Null
        Start-Sleep -Seconds 5
    }
    Start-Sleep -Seconds 10
}
