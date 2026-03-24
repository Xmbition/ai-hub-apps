$ErrorActionPreference = "Stop"

Write-Host "Creating Virtual Environment"
. "scripts/util/env_create.ps1" --python=C:\Python\python.exe --venv=C:\Qaiha\qaiha-dev --no-sync

Write-Host "Installing Python Deps"
python scripts/build_and_test.py --venv $env:VENV_PATH install_deps

Write-Host "Activating Virtual Env ($env:VENV_PATH)"
. "$env:VENV_PATH`\Scripts\Activate.ps1"

Write-Host "Configuring Hub Credentials"
qai-hub configure --api_token "$env:HUB_USER_TOKEN_PROD" --no-verbose

Write-Host "Running Tests"
Set-Location "python"; python -m pytest --pyargs qai_hub_apps.test.test_apps -s -vv -k windows

exit $LASTEXITCODE
