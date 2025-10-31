param(
  [Parameter(Mandatory=$true)][string]$InputText,
  [string]$Context = "",
  [string]$SystemHint = "Ты Jarvis LLM Core. Отвечай ТОЛЬКО одним JSON-объектом по схеме:{
  ""ok"":true,""ts"":""<ISO8601>"",""intent"":""chat"",""reply"":""краткий текст"",""speak"":""что озвучить"",""meta"":{""model"":"""",""lang"":""ru""}
} Никакого лишнего текста. Если не уверен — ok=false и короткое объяснение в reply."
)

# Консоль на всякий случай в UTF-8 (если запускали отдельно)
try {
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [Console]::InputEncoding  = $utf8
  [Console]::OutputEncoding = $utf8
} catch {}

# --- Load .env
$map = @{}
$envFile = "C:\JarvisBridge\.env"
if (Test-Path $envFile) {
  (Get-Content $envFile -Raw) -split "`r?`n" | ForEach-Object {
    if ($_ -match '^\s*#') { return }
    if ($_ -match '^\s*([\w\.\-]+)\s*=\s*(.*)\s*$') { $map[$matches[1]]=$matches[2] }
  }
}
function Get-Env([string]$k,[string]$d=""){ if($map.ContainsKey($k) -and $map[$k]){$map[$k]}else{$d} }

$apiKey  = Get-Env "OPENAI_API_KEY"
$model   = Get-Env "LLM_MODEL" "gpt-4o"
$timeout = [int](Get-Env "LLM_TIMEOUT" "30")
$log     = Get-Env "LLM_LOG" "C:\JarvisBridge\logs\llm_core.log"

if (-not $apiKey -or $apiKey -eq "PUT_YOUR_OPENAI_KEY_HERE") {
  $out = @{ ok=$false; ts=(Get-Date).ToString("o"); intent="error"; reply="OPENAI_API_KEY отсутствует"; speak="Ключ API отсутствует"; meta=@{model=$model;lang="ru"} } | ConvertTo-Json -Depth 10 -Compress
  Write-Output $out
  exit 1
}

# --- Build request
$uri = "https://api.openai.com/v1/chat/completions"
$headers = @{ Authorization = "Bearer $apiKey"; "Content-Type"="application/json" }

$sys = $SystemHint
if ($Context -and $Context.Trim().Length -gt 0) { $sys = $sys + "`nКонтекст: " + $Context.Trim() }

$bodyObj = @{
  model = $model
  messages = @(
    @{ role="system"; content=$sys },
    @{ role="user";   content=$InputText }
  )
  response_format = @{ type = "json_object" }
  temperature = 0
}
$body = ($bodyObj | ConvertTo-Json -Depth 10)

# --- Send with tiny retry
$attempt=0; $max=2; $resp=$null; $errMsg=$null
while ($attempt -le $max) {
  try {
    $attempt++
    $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -TimeoutSec $timeout
    break
  } catch {
    $errMsg = $_.Exception.Message
    if ($attempt -lt $max) { Start-Sleep -Milliseconds 400 } else { break }
  }
}

$tsNow = (Get-Date).ToString("o")
if ($resp -and $resp.choices -and $resp.choices[0].message.content) {
  $json = $resp.choices[0].message.content

  # --- Normalize to required schema ---
  try      { $obj = $json | ConvertFrom-Json }
  catch    { $obj = $null }
  if (-not $obj) {
    $obj = @{ ok=$false; ts=$tsNow; intent="error"; reply="LLM вернул не-JSON"; speak="Ошибка формата"; meta=@{model=$model;lang="ru"} }
  }
  if (-not ($obj -is [psobject])) {
    $obj = @{ ok=$false; ts=$tsNow; intent="error"; reply="LLM вернул некорректные данные"; speak="Ошибка формата"; meta=@{model=$model;lang="ru"} }
  }

  if ($null -eq $obj.ok)     { $obj | Add-Member -NotePropertyName ok     -NotePropertyValue $true -Force }
  if (-not $obj.ts)          { $obj | Add-Member -NotePropertyName ts     -NotePropertyValue $tsNow -Force }
  if (-not $obj.intent)      { $obj | Add-Member -NotePropertyName intent -NotePropertyValue "chat" -Force }
  if ($null -eq $obj.reply)  { $obj | Add-Member -NotePropertyName reply  -NotePropertyValue ""     -Force }
  if ($null -eq $obj.speak)  { $obj | Add-Member -NotePropertyName speak  -NotePropertyValue $obj.reply -Force }
  if (-not $obj.meta)        { $obj | Add-Member -NotePropertyName meta   -NotePropertyValue (@{model=$model;lang="ru"}) -Force }
  elseif (-not $obj.meta.model) { $obj.meta | Add-Member -NotePropertyName model -NotePropertyValue $model -Force }
  if (-not $obj.meta.lang)   { $obj.meta | Add-Member -NotePropertyName lang -NotePropertyValue "ru" -Force }

  $json = $obj | ConvertTo-Json -Depth 10 -Compress

  $logLine = @{ t=$tsNow; kind="llm_core_call"; req=@{model=$model; len=$InputText.Length}; resp=@{content=$json} } | ConvertTo-Json -Depth 10
  Add-Content -Path $log -Value $logLine -Encoding UTF8
  Write-Output $json
  exit 0
}
else {
  if (-not $errMsg) { $errMsg = "unknown" }
  $fail = @{ ok=$false; ts=$tsNow; intent="error"; reply=("Ошибка LLM: " + $errMsg); speak="Ошибка ядра ЛЛМ"; meta=@{model=$model;lang="ru"} }
  $failJson = $fail | ConvertTo-Json -Depth 10 -Compress
  Add-Content -Path $log -Value (@{ t=$tsNow; kind="llm_core_error"; error=$errMsg } | ConvertTo-Json -Depth 5) -Encoding UTF8
  Write-Output $failJson
  exit 2
}
