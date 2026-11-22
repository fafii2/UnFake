$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$environmentPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$environmentWorks = $false
if (Test-Path -LiteralPath $environmentPython) {
    try {
        & $environmentPython -c 'import sys; assert sys.version_info >= (3, 10)' *> $null
        $environmentWorks = $LASTEXITCODE -eq 0
    } catch { $environmentWorks = $false }
}
if (-not $environmentWorks) {
    $environmentDirectory = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.venv'))
    $projectDirectory = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
    if (-not $environmentDirectory.StartsWith($projectDirectory, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Environment path must remain inside the UnFake project.'
    }
    if (Test-Path -LiteralPath $environmentDirectory) {
        Move-Item -LiteralPath $environmentDirectory -Destination ($environmentDirectory + '.backup-' + (Get-Date -Format 'yyyyMMddHHmmss'))
    }
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $runtimePython = $env:CODEX_PRIMARY_RUNTIME_PYTHON
    $registeredRuntime = if (Get-Command Get-AppxPackage -ErrorAction SilentlyContinue) {
        Get-AppxPackage -Name '*CodexPrimaryRuntime*' -ErrorAction SilentlyContinue |
            Sort-Object Version -Descending | Select-Object -First 1
    }
    $registeredPython = if ($registeredRuntime) { Join-Path $registeredRuntime.InstallLocation 'dependencies\python\python.exe' }
    $pythonCandidates = @($runtimePython, $registeredPython, $bundledPython, 'py', 'python') | Where-Object { $_ }
    $selectedPython = $null
    foreach ($candidate in $pythonCandidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            # Ignore Windows Store aliases, which can open the Store instead of Python.
            if ($command.Source -match '\\Microsoft\\WindowsApps\\python3?\.exe$') { continue }
            try {
                & $command.Source -c 'import sys; assert sys.version_info >= (3, 10)' *> $null
                if ($LASTEXITCODE -eq 0) { $selectedPython = $command.Source; break }
            } catch { continue }
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
