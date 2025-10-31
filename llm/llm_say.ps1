param(
  [Parameter(Mandatory=$true)][string]$Text
)

# UTF-8 безопасный вывод
try {
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [Console]::InputEncoding  = $utf8
  [Console]::OutputEncoding = $utf8
} catch {}

$ts = (Get-Date).ToString("HH:mm:ss")
Write-Host "`n[$ts] Jarvis → LLM: $Text" -ForegroundColor Cyan

# Вызов ядра
$resp = & $PSScriptRoot\llm_core.ps1 -InputText $Text
if (-not $resp) {
  Write-Host "[LLM-SAY][ERROR] ядро не вернуло ответ" -ForegroundColor Red
  exit 1
}

# Попытка распарсить JSON
try { $obj = $resp | ConvertFrom-Json } catch { $obj = $null }

if (-not $obj) {
  Write-Host "[LLM-SAY][ERROR] Неверный формат JSON:" -ForegroundColor Red
  Write-Host $resp
  exit 2
}

# Красивый вывод
if ($obj.ok -eq $true) {
  $reply = $obj.reply
  $speak = $obj.speak
  Write-Host "[LLM] reply: $reply" -ForegroundColor Green
  Write-Host "[LLM] speak: $speak" -ForegroundColor Yellow
} else {
  Write-Host "[LLM] ❌ Ошибка: $($obj.reply)" -ForegroundColor Red
}

# Возврат JSON целиком (для пайплайна)
$resp
