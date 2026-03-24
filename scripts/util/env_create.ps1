# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

$origErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Stop"

$ENV_PATH = "qaiha-dev"
$SYNC = 1          # Sync is ON by default → we will FAIL unless user disables it (no env_sync.ps1)
$PYTHON = "python"

foreach ($arg in $args) {
    if ($arg -like "--venv=*") {
        $ENV_PATH = $arg -replace "^--venv=", ""
    }
    elseif ($arg -eq "--no-sync") {
        $SYNC = 0
    }
    elseif ($arg -like "--python=*") {
        $PYTHON = $arg -replace "^--python=", ""
    }
    else {
        Write-Error "Bad opt $arg."
        exit 1
    }
}

if ($SYNC -eq 1) {
    Write-Error ":x: Sync mode is not allowed in this environment. Re-run with --no-sync."
    exit 1
}

if (-not (Test-Path $ENV_PATH)) {
    $parent = Split-Path $ENV_PATH -Parent
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }

    Write-Host "Creating virtual env $ENV_PATH."
    & $PYTHON -m venv $ENV_PATH

    Write-Host "Activating virtual env."
    & "$ENV_PATH\Scripts\Activate.ps1"
}
else {
    & "$ENV_PATH\Scripts\Activate.ps1"
    Write-Host "Env created already. Skipping creation."
}

$ErrorActionPreference = $origErrorActionPreference
