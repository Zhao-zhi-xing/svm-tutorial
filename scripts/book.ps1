param(
  [ValidateSet('preview','render','prepare','validate','serve','check')]
  [string]$Action='preview',
  [string]$PythonPath='',
  [string]$RPath=''
)
$ErrorActionPreference='Stop'
$bookRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $bookRoot
if (-not $PythonPath) {
  if ($env:RETICULATE_PYTHON) { $PythonPath=$env:RETICULATE_PYTHON }
  elseif (Test-Path -LiteralPath '.venv/Scripts/python.exe') { $PythonPath=(Resolve-Path '.venv/Scripts/python.exe').Path }
  elseif (Test-Path -LiteralPath "$env:USERPROFILE/anaconda3/python.exe") { $PythonPath=Join-Path $env:USERPROFILE 'anaconda3/python.exe' }
  else { $PythonPath=(Get-Command python -ErrorAction Stop).Source }
}
if ($Action -eq 'serve') {
  & $PythonPath -m http.server 4317 --bind 127.0.0.1 --directory _book
  exit $LASTEXITCODE
}
if (-not $RPath) {
  if ($env:QUARTO_R) { $RPath=$env:QUARTO_R }
  else {
    $rCommand=Get-Command Rscript -ErrorAction SilentlyContinue
    if ($rCommand) { $RPath=$rCommand.Source }
    else { $RPath=(Get-ChildItem -Path "$env:ProgramFiles/R/*/bin/Rscript.exe" | Sort-Object FullName -Descending | Select-Object -First 1).FullName }
  }
}
if (-not $RPath) { throw 'Rscript not found. Set -RPath or QUARTO_R.' }
$env:RETICULATE_PYTHON=$PythonPath
$env:QUARTO_PYTHON=$PythonPath
$env:QUARTO_R=$RPath
$env:SVM_R_LIBRARY=Join-Path $bookRoot '.R-library'
$env:R_LIBS_USER=$env:SVM_R_LIBRARY
$env:R_PROFILE_USER=Join-Path $bookRoot 'scripts/r-profile.R'
$env:PYTHONIOENCODING='utf-8'
$env:RETICULATE_USE_MANAGED_VENV='no'
$quartoPath=Join-Path $bookRoot '.tools/bin/quarto.cmd'
if (Test-Path -LiteralPath '.tools/runtime-path.txt') {
  $runtimePath=(Get-Content -LiteralPath '.tools/runtime-path.txt' -Raw).Trim()
  if (Test-Path -LiteralPath $runtimePath) { $quartoPath=$runtimePath }
}
if (-not (Test-Path -LiteralPath $quartoPath)) { $quartoPath=(Get-Command quarto -ErrorAction Stop).Source }
switch ($Action) {
  'preview' { & $quartoPath preview --port 4317 --no-browser }
  'render' { & $quartoPath render }
  'check' { & $quartoPath check }
  'prepare' {
    & $PythonPath scripts/prepare.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $RPath scripts/export_khan.R
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $PythonPath scripts/validate.py
  }
  'validate' {
    & $PythonPath -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $PythonPath scripts/validate.py
  }
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
