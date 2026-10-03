param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -and $PSVersionTable.PSEdition -ne 'Desktop') { throw 'Build the Windows package on Windows.' }
$workspace = Split-Path -Parent $PSScriptRoot
Push-Location $workspace
try {
    if (-not (Test-Path -LiteralPath '.packaging-venv\Scripts\python.exe')) {
        & $Python -m venv .packaging-venv
        if ($LASTEXITCODE -ne 0) { throw 'Packaging environment creation failed.' }
    }
    & .\.packaging-venv\Scripts\python.exe -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Packaging dependency installation failed.' }
    & .\.packaging-venv\Scripts\python.exe -m PyInstaller --clean --noconfirm CharactersUnlimited.spec
    if ($LASTEXITCODE -ne 0) { throw 'Windows packaging failed.' }
    Copy-Item -LiteralPath docs\windows-package.md -Destination dist\CharactersUnlimited\START-HERE.md
    Write-Output 'Package ready: dist\CharactersUnlimited\CharactersUnlimited.exe'
} finally { Pop-Location }
