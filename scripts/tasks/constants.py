# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

import os
import sys
from pathlib import Path

DEFAULT_PYTHON = sys.executable

# Repository
REPO_ROOT = Path(os.path.basename(__file__)).parent.parent
VENV_PATH = os.path.join(REPO_ROOT, "qaiha-dev")
BUILD_ROOT = os.path.join(REPO_ROOT, "build")
