# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

from collections.abc import ValuesView
from pathlib import Path
from typing import Any

from qai_hub_apps.configs.registry_yaml import AppInfo, AppRegistry

__all__ = ["App", "Registry"]


class App:
    """CLI-layer wrapper around AppInfo. Owns presentation logic."""

    def __init__(self, info: AppInfo) -> None:
        self._info = info

    def __getattr__(self, name: str) -> Any:
        # Transparently delegate field access to the underlying AppInfo.
        return getattr(self._info, name)

    def detail_fields(self) -> list[tuple[str, str]]:
        fields: list[tuple[str, str]] = [
            ("ID", self._info.id or "-"),
            ("Type", self._info.app_type),
        ]
        if self._info.runtime:
            fields.append(("Runtime", self._info.runtime.value))
        if self._info.domain:
            fields.append(("Domain", self._info.domain))
        if self._info.use_case:
            fields.append(("Use Case", self._info.use_case))
        if self._info.precisions:
            fields.append(
                ("Precisions", ", ".join(p.value for p in self._info.precisions))
            )
        if self._info.related_models:
            fields.append(
                ("Models", ", ".join(str(m) for m in self._info.related_models))
            )
        return fields


class Registry:
    """CLI-layer wrapper around AppRegistry. Singleton — one instance per process."""

    _instance: Registry | None = None

    def __init__(self, raw: AppRegistry) -> None:
        self._raw = raw
        self._apps = {a.id: App(a) for a in raw.apps}

    @classmethod
    def load(cls, path: str | Path) -> Registry:
        if cls._instance is None:
            cls._instance = cls(AppRegistry.from_yaml(Path(path)))
        return cls._instance

    @classmethod
    def load_bundled(cls) -> Registry:
        return cls.load(Path(__file__).parent.parent / "configs" / "registry.yaml")

    @property
    def apps(self) -> ValuesView[App]:
        return self._apps.values()

    def find_by_id(self, app_id: str) -> App | None:
        return self._apps.get(app_id.lower(), None)
