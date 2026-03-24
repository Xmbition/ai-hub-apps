#!/usr/bin/env bash
# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
# shellcheck source=/dev/null

REPO_ROOT=$(git rev-parse --show-toplevel)

. "${REPO_ROOT}/scripts/util/common.sh"

set_strict_mode


cd "$(dirname "$0")/../.."

venv="${VENV_PATH:-qaiha-dev}"
echo "Activating venv in ${venv}"
source "${venv}/bin/activate"

paths=(apps)
for path in "${paths[@]}"; do
    pathToCheck="${path}"
    echo "Running mypy on ${pathToCheck}"
    mypy --ignore-missing-imports --explicit-package-bases --warn-unused-configs --config-file="${REPO_ROOT}/mypy.ini" "${pathToCheck}"
done
