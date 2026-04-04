# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
import os
from functools import lru_cache
from pathlib import Path

from platformdirs import user_cache_dir

# Repository Global Paths
REPOSITORY_ROOT = Path(os.path.dirname(__file__)).parent.parent.parent.parent
CACHE_ROOT = Path(user_cache_dir("qaiha"))
APPS_ROOT = REPOSITORY_ROOT / "apps"
MAX_APP_SEARCH_DEPTH = 3


def is_app_root(path: str | os.PathLike) -> bool:
    return (Path(path) / "info.yaml").exists()


def _get_all_apps(
    base: str | os.PathLike = APPS_ROOT,
    root: str | os.PathLike = APPS_ROOT,
    depth: int = 0,
) -> list[Path]:
    if depth >= MAX_APP_SEARCH_DEPTH:
        return []

    app_dirs = []
    for filename in os.listdir(root):
        path = Path(root) / filename
        if os.path.isdir(path):
            if is_app_root(path):
                app_dirs.append(path.relative_to(base))
            else:
                app_dirs.extend(_get_all_apps(base, path, depth + 1))

    return app_dirs


@lru_cache
def get_all_apps(
    subdir: str | os.PathLike | None = None, apps_root: str | os.PathLike = APPS_ROOT
) -> list[Path]:
    """
    Get path to every app relative to the given root directory.

    Parameters
    ----------
    subdir:
        Subdirectory under the application root for which to recursively look for apps.

    apps_root:
        Absolute path to the root of all AI Hub Apps applications.

    Returns
    -------
    list[Path]
        A list of relative paths to each application directory.
        Each path is relative to the AI Hub Apps application root.

    Notes
    -----
    An app root is identified by whether it contains an `info.yaml` that can be parsed by QIAHAAppInfo.
    """
    return _get_all_apps(apps_root, APPS_ROOT / subdir if subdir else APPS_ROOT, 0)
