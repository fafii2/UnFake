$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$environmentPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $environmentPython)) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $pythonCandidates = @($bundledPython, 'py', 'python')
    $selectedPython = $null
    foreach ($candidate in $pythonCandidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            & $command.Source -c 'import sys; assert sys.version_info >= (3, 10)' 2>$null
            if ($LASTEXITCODE -eq 0) { $selectedPython = $command.Source; break }
        }
    }
    if (-not $selectedPython) { throw 'Install Python 3.10 or newer, then run Setup-UnFake.ps1 again.' }
    & $selectedPython -m venv .venv
    if ($LASTEXITCODE -ne 0 -and (Test-Path -LiteralPath $environmentPython)) {
        & $selectedPython -m pip --python $environmentPython install pip
        if ($LASTEXITCODE -ne 0) { throw 'Could not prepare the Python environment.' }
    } elseif ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& $environmentPython -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        & $bundledPython -m pip --python $environmentPython install pip
        if ($LASTEXITCODE -ne 0) { throw 'Could not install pip.' }
    } else { throw 'The Python environment is missing pip. Recreate it using a standard Python installation.' }
}
& $environmentPython -m pip install -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (-not (Test-Path -LiteralPath 'backend\.env')) {
    Copy-Item -LiteralPath 'backend\.env.example' -Destination 'backend\.env'
}
Push-Location backend
try {
    & $environmentPython -m scripts.seed_archive
    if ($LASTEXITCODE -ne 0) { throw 'Archive preparation failed.' }
} finally { Pop-Location }
Write-Host 'UnFake is ready. Run Start-UnFake.cmd, then load the extension folder in Chrome or Edge.'
