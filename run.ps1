$ErrorActionPreference = 'Stop'
if (Test-Path '.venv\Scripts\python.exe') {
  & '.venv\Scripts\python.exe' -m pip install -r requirements.txt
  & '.venv\Scripts\python.exe' -m backend.app
} else {
  Write-Host 'Using system Python (no .venv required).'
  python -m pip install -r requirements.txt
  python -m backend.app
}
