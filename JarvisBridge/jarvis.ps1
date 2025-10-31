# ============================================================
# JarvisBridge — голосовой ассистент для управления ПК
# Автор: Матвей и ChatGPT 🧠
# Версия: совместима с PowerShell 5.1+
# ============================================================

Add-Type -AssemblyName System.Speech
Add-Type -AssemblyName PresentationFramework

# === Настройки ===
$cfgFile = "C:\JarvisBridge\JarvisBridge\commands.json"
if (-not (Test-Path $cfgFile)) {
    Write-Host "⚠️ Файл конфигурации не найден: $cfgFile"
    exit
}

try {
    $cfg = Get-Content -Raw -Path $cfgFile | ConvertFrom-Json
} catch {
    Write-Host "⚠️ Ошибка чтения JSON. Проверь синтаксис."
    exit
}

# === Порог уверенности ===
$threshold = 0.7
if ($cfg.PSObject.Properties.Name -contains 'confidence_threshold' -and $cfg.confidence_threshold) {
    try { $threshold = [double]$cfg.confidence_threshold } catch {}
}

# === Язык распознавания ===
$culture = "ru-RU"
if ($cfg.PSObject.Properties.Name -contains 'culture' -and $cfg.culture) {
    $culture = $cfg.culture
}

$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine($culture)
$recognizer.SetInputToDefaultAudioDevice()

# === Список команд ===
if (-not $cfg.commands) {
    Write-Host "⚠️ Нет списка команд в JSON!"
    exit
}

# === Добавление грамматики ===
$choices = New-Object System.Speech.Recognition.Choices
foreach ($cmd in $cfg.commands) {
    $choices.Add($cmd.phrase)
}

$grammarBuilder = New-Object System.Speech.Recognition.GrammarBuilder
$grammarBuilder.Culture = [System.Globalization.CultureInfo]::GetCultureInfo($culture)
$grammarBuilder.Append($choices)

$grammar = New-Object System.Speech.Recognition.Grammar($grammarBuilder)
$recognizer.LoadGrammar($grammar)

# === Действия ===
function Run-Action($cmd) {
    $type = $cmd.action.ToLower()
    $target = $cmd.target

    switch ($type) {
        'url'     { Start-Process $target | Out-Null }
        'folder'  { Start-Process $target | Out-Null }
        'exe'     { if (Test-Path $target) { Start-Process -FilePath $target | Out-Null } }
        'shell'   { Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList "-NoProfile -Command $target" | Out-Null }
        default   { Write-Host "⚠️ Неизвестный тип действия: $type" }
    }
}

# === Обработка распознанного ===
$recognizer.SpeechRecognized += {
    param($sender, $eventArgs)

    $text = $eventArgs.Result.Text
    $conf = $eventArgs.Result.Confidence

    if ($conf -ge $threshold) {
        Write-Host "🎤 Распознано: '$text' ($([math]::Round($conf,2)))"
        $cmd = $cfg.commands | Where-Object { $_.phrase -eq $text }
        if ($cmd) {
            Run-Action $cmd
        }
    } else {
        Write-Host "🤔 Неуверен ($([math]::Round($conf,2))) — '$text'"
    }
}

# === Запуск ===
Write-Host ""
Write-Host "🟢 JarvisBridge запущен. Скажи: 'джарвис открой ютуб' или 'включи музыку'"
Write-Host "ℹ️ Порог уверенности: $threshold | Язык: $culture"
Write-Host "⏸ Нажми Ctrl+C для выхода."
Write-Host ""

$recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)

# === Ожидание завершения ===
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    $recognizer.RecognizeAsyncStop()
}
