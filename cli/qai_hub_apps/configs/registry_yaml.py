# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

from datetime import datetime

from packaging.version import Version
from pydantic import model_validator
from qai_hub_models_cli.common import Precision, TargetRuntime

from qai_hub_apps import __version__
from qai_hub_apps.configs.base_config import BaseConfig


class AppInfo(BaseConfig):
    name: str
    id: str
    status: str
    headline: str
    description: str
    domain: str
    use_case: str
    app_repo_url: str
    app_type: str
    runtime: TargetRuntime
    related_models: list[str]
    precisions: list[Precision]


class AppRegistry(BaseConfig):
    schema_version: str
    min_cli_version: str
    generated_at: datetime
    apps: list[AppInfo]

    @model_validator(mode="after")
    def _unique_ids(self) -> AppRegistry:
        ids = [a.id for a in self.apps]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"Registry contains duplicate app IDs: {sorted(dupes)}")
        return self

    @model_validator(mode="after")
    def _check_min_cli_version(self) -> AppRegistry:
        if Version(__version__) < Version(self.min_cli_version):
            raise ValueError(
                f"This registry requires qai-hub-apps >= {self.min_cli_version}, "
                f"but you have {__version__}. Please upgrade: pip install -U qai-hub-apps"
            )
        return self
