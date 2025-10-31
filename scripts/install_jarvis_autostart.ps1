# Установка автозапуска Jarvis при старте Windows
# Запускать этот файл нужно из PowerShell (Администратор)

$ErrorActionPreference = "Stop"

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

$CmdPath     = Join-Path $ScriptDir "run_jarvis_hotword.cmd"
$VbsPath     = Join-Path $ScriptDir "run_silently.vbs"

if (!(Test-Path $CmdPath)) { throw "Не найден $CmdPath" }
if (!(Test-Path $VbsPath)) { throw "Не найден $VbsPath" }

$TaskName = "Jarvis Always-On"

$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`" `"$CmdPath`"" -WorkingDirectory $ProjectRoot
$TriggerBoot  = New-ScheduledTaskTrigger -AtStartup
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
  -MultipleInstances IgnoreNew `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -RestartCount 9999 `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Hours 0)

$Principal = New-ScheduledTaskPrincipal -UserId "$env:UserName" -LogonType Interactive -RunLevel Highest

$Task = New-ScheduledTask -Action $Action -Trigger @($TriggerBoot, $TriggerLogon) -Settings $Settings -Principal $Principal

try {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
} catch {}

Register-ScheduledTask -TaskName $TaskName -InputObject $Task | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "[OK] Установлено задание '$TaskName'. Jarvis будет запускаться при старте системы и входе пользователя, с авто-перезапуском при сбоях."
