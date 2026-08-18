<# Reproduce the immutable TopVenues profile on native Windows PowerShell. #>
param(
    [string]$Profile = "security-20",
    [string]$PythonCommand = "",
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if ($Profile -ne "security-20") { throw "This release exposes only the immutable security-20 profile." }

# Prefer the Windows launcher pinned to the supported minor version.  On many
# Windows hosts `python` still resolves to an older, system-wide installation.
$python = $null
$pythonArgs = @()
if ($PythonCommand) {
    $python = Get-Command $PythonCommand -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
        if ($LASTEXITCODE -ne 0) { $python = $null }
    }
} else {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if ($null -ne $python -and -not $PythonCommand) {
    foreach ($minor in @("3.12", "3.11")) {
        & $python.Source "-$minor" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
        if ($LASTEXITCODE -eq 0) {
            $pythonArgs = @("-$minor")
            break
        }
    }
    if ($pythonArgs.Count -eq 0) { $python = $null }
}
if ($null -eq $python -and -not $PythonCommand) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $python) {
        & $python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
        if ($LASTEXITCODE -ne 0) { $python = $null }
    }
}
if ($null -eq $python) {
    throw "Python 3.11+ is required. Install Python 3.11 or 3.12 from python.org, then rerun."
}

if (-not (Test-Path ".venv")) {
    if ($SkipInstall) { throw "-SkipInstall requires an existing .venv." }
    & $python.Source @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python virtual environment." }
}
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "The existing .venv is not native Windows. Remove only .venv and rerun; do not remove corpus data."
}
& $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "The existing .venv uses Python older than 3.11. Remove only .venv and rerun; do not remove corpus data."
}
if (-not $SkipInstall) {
    & $venvPython -m pip install --disable-pip-version-check --prefer-binary -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
}
& $venvPython scripts\verify_profile_snapshot.py --profile $Profile
if ($LASTEXITCODE -ne 0) { throw "Snapshot manifest verification failed." }
# A concurrent reproduction is serialized; a Windows file lock is reported clearly.
& $venvPython -m src.cli --profile $Profile refresh-db
if ($LASTEXITCODE -ne 0) { throw "Database refresh failed." }
& $venvPython -m src.cli --profile $Profile stats
if ($LASTEXITCODE -ne 0) { throw "Statistics check failed." }
& $venvPython -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Test suite failed." }
& $venvPython scripts\benchmark_search.py --profile $Profile --trials 11
if ($LASTEXITCODE -ne 0) { throw "Search exercise failed." }
$sample = Join-Path ([System.IO.Path]::GetTempPath()) ("topvenues_repro_" + [guid]::NewGuid().ToString() + ".bib")
try {
    & $venvPython -m src.cli --profile $Profile export --title intrusion --format bibtex --output $sample
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $sample) -or (Get-Item $sample).Length -le 1000) { throw "BibTeX export check failed." }
} finally { Remove-Item $sample -ErrorAction SilentlyContinue }
Write-Host "Profile $Profile reproduced successfully on native Windows PowerShell."
