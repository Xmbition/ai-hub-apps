# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterable
from sys import platform

from .constants import DEFAULT_PYTHON, REPO_ROOT
from .task import RunCommandsTask, RunCommandsWithVenvTask
from .util import get_pip


class CreateVenvTask(RunCommandsTask):
    def __init__(self, venv_path: str, python_executable: str | None = None) -> None:
        if platform == "win32":
            super().__init__(
                f"Creating virtual environment at {venv_path}",
                f"{REPO_ROOT}/scripts/util/env_create.ps1 --python={python_executable or DEFAULT_PYTHON} --venv={venv_path} --no-sync",
            )
        else:
            super().__init__(
                f"Creating virtual environment at {venv_path}",
                f"source {REPO_ROOT}/scripts/util/env_create.sh --python={python_executable or DEFAULT_PYTHON} --venv={venv_path} --no-sync",
            )


class SyncLocalQAIHAVenvTask(RunCommandsWithVenvTask):
    """Sync the provided environment with local ai-hub-apps python package."""

    def __init__(
        self,
        venv_path: str | None,
        extras: Iterable[str] = [],
    ) -> None:
        extras_str = f"[{','.join(extras)}]" if extras else ""
        super().__init__(
            f"Create Local QAIHA{extras_str} Virtual Environment at {venv_path}",
            venv_path,
            [
                # Install torch CPU first, since this is an AI Hub Models requirement
                # and the default is to fetch torch with CUDA.
                f"{get_pip()} install torch~=2.8.0 --index-url https://download.pytorch.org/whl/cpu",
                # Install AI Hub Apps + AI Hub Models
                f"{get_pip()} install -e {REPO_ROOT}/python{extras_str}",
            ],
        )
