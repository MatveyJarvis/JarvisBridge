param(
  [ValidateSet('voice','text')]
  [string]$mode = '',
  [string]$file = ''
)

$ErrorActionPreference = 'Stop'

# normalize file path (if provided)
$absFile = ''
if ($file) {
  try { $absFile = (Resolve-Path -Path $file).Path } catch { $absFile = $file }
}

# goto jarvis_min next to this script
$root = Split-Path -Parent $PSScriptRoot
Set-Location -Path (Join-Path $root 'jarvis_min')

# venv + deps
if (!(Test-Path '.\venv')) { python -m venv venv }
. '.\venv\Scripts\Activate.ps1'
pip install -r requirements.txt > $null

# ask mode if not provided
if (-not $mode) {
  Write-Host ''
  Write-Host '[1] Voice   [2] Text'
  $k = Read-Host 'Choose mode'
  if ($k -eq '1') { $mode = 'voice' }
  elseif ($k -eq '2') { $mode = 'text' }
  else { Write-Host 'Cancel'; exit 0 }
}

switch ($mode) {
  'voice' { if ($absFile) { python .\main.py --file $absFile } else { python .\main.py } }
  'text'  { python .\main_text.py }
}
