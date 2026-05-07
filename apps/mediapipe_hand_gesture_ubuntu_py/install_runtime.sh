#!/usr/bin/env bash
# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ../../_shared/scripts/python_utils.sh
source ../../_shared/scripts/apt_utils.sh
source ../../_shared/scripts/pip_utils.sh
source ../../_shared/scripts/qairt_utils.sh

install_python
install_qairt

install_apt_pkgs \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-tools \
    libcairo2-dev \
    python3-gi \
    python3-gi-cairo
install_apt_pkg gir1.2-gstreamer-1.0

install_pip_deps -r "$SCRIPT_DIR/requirements.txt"
