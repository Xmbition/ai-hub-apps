# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
$ErrorActionPreference = "Stop"

. ..\..\_shared\scripts\python_utils.ps1
. ..\..\_shared\scripts\winget_utils.ps1
. ..\..\_shared\scripts\pip_utils.ps1

Install-Python
Install-WingetPackage -Id "Microsoft.Git"
Install-PipDeps -Packages @("-r", (Join-Path $PSScriptRoot "requirements.txt"))
