# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

import sys

from qai_hub_apps.registry import App, Registry


def _print_detail(app: App) -> None:
    print(app.name)
    print("\u2550" * 50)
    print()
    for label, value in app.detail_fields():
        print(f"{label + ':':<12}{value}")
    print()
    if app.headline:
        print(f"{app.headline}\n")
    if app.description:
        print(f"{app.description}\n")
    if app.app_repo_url:
        print(f"Repo:  {app.app_repo_url}")


def run_list(registry: Registry) -> None:
    apps = registry.apps

    print(f"Qualcomm\u00ae AI Hub Apps  ({len(apps)} apps)\n")
    id_w, name_w = 38, 38
    header = f"{'ID':<{id_w}}  {'Name':<{name_w}}"
    print(header)
    print("\u2500" * len(header))
    for app in apps:
        app_id = (app.id or app.name) or ""
        print(f"{app_id:<{id_w}}  {app.name:<{name_w}}")


def run_info(app_id: str, registry: Registry) -> None:
    app = registry.find_by_id(app_id)
    if app is None:
        print(
            f"Error: app '{app_id}' not found. Run 'qai-hub-apps list' to see available app IDs."
        )
        sys.exit(1)
    _print_detail(app)
