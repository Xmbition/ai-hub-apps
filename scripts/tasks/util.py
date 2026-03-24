# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

from __future__ import annotations

import contextlib
import functools
import os
import shutil
import subprocess
from sys import platform
from typing import Optional

if platform == "win32":
    SHELL_EXECUTABLE = shutil.which("powershell")
else:
    SHELL_EXECUTABLE = shutil.which("bash")


class Colors:
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[0;33m"
    OFF = "\033[0m"


@contextlib.contextmanager
def new_cd(x):
    d = os.getcwd()

    # This could raise an exception, but it's probably
    # best to let it propagate and let the caller
    # deal with it, since they requested x
    os.chdir(x)

    try:
        yield

    finally:
        # This could also raise an exception, but you *really*
        # aren't equipped to figure out what went wrong if the
        # old working directory can't be restored.
        os.chdir(d)


# Convenience function for printing to stdout without buffering.
def echo(value, **args):
    print(value, flush=True, **args)


def have_root() -> bool:
    return os.geteuid() == 0


def run(command):
    return subprocess.run(command, shell=True, check=True, executable=SHELL_EXECUTABLE)


def str_to_bool(word: str) -> bool:
    return word.lower() in ["1", "true", "yes"]


def get_env_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    val = os.environ.get(key, None)
    if val is None:
        return None
    return str_to_bool(val)


def on_ci() -> bool:
    return get_env_bool("QAIHM_CI") or False


def debug_mode() -> bool:
    return get_env_bool("DEBUG_MODE") or False


@functools.cache
def uv_installed() -> bool:
    return shutil.which("uv") is not None


@functools.cache
def get_pip() -> str:
    if uv_installed():
        return "uv pip"
    else:
        return "pip"
