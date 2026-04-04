# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
import os
from enum import Enum, unique
from pathlib import Path

from pydantic import ConfigDict, Field
from qai_hub_apps_test.utils.paths import APPS_ROOT, REPOSITORY_ROOT
from qai_hub_models.configs.info_yaml import MODEL_LICENSE as LICENSE
from qai_hub_models.models.common import Precision, TargetRuntime
from qai_hub_models.scorecard.device import ScorecardDevice, cs_8_gen_3, cs_x_elite
from qai_hub_models.utils.base_config import BaseQAIHMConfig
from typing_extensions import assert_never


@unique
class AppStatus(Enum):
    UNPUBLISHED = "unpublished"
    PUBLISHED = "published"


@unique
class AppType(Enum):
    ANDROID = "android"
    WINDOWS = "windows"
    UBUNTU = "ubuntu"

    @property
    def default_device(self) -> ScorecardDevice:
        if self == AppType.ANDROID:
            return cs_8_gen_3
        elif self == AppType.WINDOWS:
            return cs_x_elite
        elif self == AppType.UBUNTU:
            return cs_x_elite  # safe-harbor; no device has ubuntu os yet
        assert_never(self)


class QAIHAAppInfo(BaseQAIHMConfig):
    model_config = ConfigDict(extra="ignore")
    ##########################
    # General Information
    ##########################

    # App name
    name: str
    status: AppStatus
    skip_test: str | None = None

    # License information
    license_url: str
    license_type: LICENSE

    # Model IDs / Precisions / Runtime this app supports
    related_models: list[str]
    precisions: list[Precision]
    runtime: TargetRuntime

    ##########################
    # Build System Information
    ##########################

    # Supported AI Hub Models version
    # If None, assumes any version is supported.
    qaihm_version: str | None = None

    # Path in which downloaded model files should be placed
    # A list can be used for multi-component models.
    model_file_paths: list[Path] = []

    # Path to private S3 URLs that CI will use to fetch certain models. map<Model ID, map<Precision, map<Chipset, Relative S3 Path>>
    # This is necessary for complex models (like LLMs) until AI Hub Models has a good way to fetch these.
    private_model_s3_paths: dict[str, dict[Precision, dict[str, str]]] = Field(
        default_factory=dict
    )

    # The type of application. Each application type uses a standard build system.
    # For example, all Android apps use Gradle and the Java SDK.
    app_type: AppType

    @staticmethod
    def from_app(path: str | os.PathLike) -> tuple["QAIHAAppInfo", Path]:
        """
        Load an app info from this directory or yaml file.

        If the path is relative, dir is assumed to be relative to qai-hub-apps/apps.
        """
        path = Path(path)
        if not os.path.isabs(path):
            if path.parts and path.parts[0] == "apps":
                path = REPOSITORY_ROOT / path
            else:
                path = APPS_ROOT / path
        yaml_path = path / "info.yaml" if os.path.isdir(path) else path
        adir = path if os.path.isdir(path) else Path(os.path.dirname(path))
        return QAIHAAppInfo.from_yaml(yaml_path), adir
