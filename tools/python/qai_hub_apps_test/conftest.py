# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

from pathlib import Path

import pytest
from qai_hub_models.configs.info_yaml import MODEL_LICENSE as LICENSE
from qai_hub_models.models.common import Precision, TargetRuntime

from qai_hub_apps_test.configs.info_yaml import AppLanguage, AppType, QAIHAAppInfo


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "bundler_unit: unit tests for bundler and generate_registry (run with -m bundler_unit)",
    )


def make_sample_app_info(**overrides: object) -> QAIHAAppInfo:
    """Factory for QAIHAAppInfo with sensible defaults. Accepts keyword overrides."""
    defaults: dict = dict(
        name="Test App",
        id="test_app",
        status="published",
        headline="Test headline",
        description="Test description",
        domain="Test",
        use_case="Testing",
        app_repo_url="https://github.com/test/app",
        app_type=AppType.UBUNTU,
        runtime=TargetRuntime.ONNX,
        related_models=["test_model"],
        precisions=[Precision.float],
        languages=[AppLanguage.PYTHON],
        license_url="https://github.com/qualcomm/ai-hub-apps/blob/main/LICENSE",
        license_type=LICENSE.BSD_3_CLAUSE,
        private_model_s3_paths={},
    )
    defaults.update(overrides)
    return QAIHAAppInfo(**defaults)


@pytest.fixture
def sample_app_info() -> QAIHAAppInfo:
    return make_sample_app_info()


@pytest.fixture
def dummy_scripts_path(tmp_path: Path) -> Path:
    """Minimal shared scripts directory mirroring apps/_shared/scripts/.

    Returns the scripts_root directory::

        tmp_path/apps/_shared/scripts/
          versions.env          # PYTHON_VERSION="3.10"
          load_versions.sh      # leaf — sourced by apt_utils.sh
          apt_utils.sh          # sources load_versions.sh (transitive dep demo)
          load_versions.ps1     # leaf — sourced by winget_utils.ps1 / pip_utils.ps1
          winget_utils.ps1      # sources load_versions.ps1
          pip_utils.ps1         # sources load_versions.ps1
    """
    scripts_root = tmp_path / "apps" / "_shared" / "scripts"
    scripts_root.mkdir(parents=True)
    (scripts_root / "versions.env").write_text('PYTHON_VERSION="3.10"\n')
    load_sh = scripts_root / "load_versions.sh"
    load_sh.write_text("# load versions\n")
    (scripts_root / "apt_utils.sh").write_text(
        f'source {load_sh}\ninstall_apt_pkg() {{ echo "$1"; }}\n'
    )
    load_ps1 = scripts_root / "load_versions.ps1"
    load_ps1.write_text("# load versions\n")
    (scripts_root / "winget_utils.ps1").write_text(
        f'. "{load_ps1}"\nfunction Install-WingetPackage {{ param($Id) }}\n'
    )
    (scripts_root / "pip_utils.ps1").write_text(
        f'. "{load_ps1}"\nfunction Install-PipDeps {{ param($R) }}\n'
    )
    (scripts_root / "unreferenced.sh").write_text("# unused\n")
    return scripts_root


@pytest.fixture
def dummy_python_app_path(tmp_path: Path) -> Path:
    """Minimal dummy Python app that imports qai_hub_apps_utils.helper.

    Returns the app root directory::

        tmp_path/my_dummy_app/
          info.yaml
          main.py           # from qai_hub_apps_utils.helper import do_something
          requirements.txt  # Pillow>=9.0
    """
    app_dir = tmp_path / "my_dummy_app"
    app_dir.mkdir()
    make_sample_app_info(id="my_dummy_app").to_yaml(
        app_dir / "info.yaml", write_if_empty=True
    )
    (app_dir / "main.py").write_text(
        "from qai_hub_apps_utils.helper import do_something\ndo_something()\n"
    )
    (app_dir / "requirements.txt").write_text("Pillow>=9.0\n")
    return app_dir


@pytest.fixture
def dummy_python_sdk_path(tmp_path: Path) -> Path:
    """Dummy qai_hub_apps_utils SDK with a transitive dependency chain.

    Returns the sdk_parent directory (the one that *contains*
    ``qai_hub_apps_utils/``)::

        tmp_path/sdk/
          qai_hub_apps_utils/
            __init__.py
            helper.py         # from qai_hub_apps_utils.math_utils import add
            math_utils.py     # leaf module
            requirements/
              requirements-helper.txt       # numpy>=1.24
              requirements-math_utils.txt   # (empty / comment only)
    """
    sdk_parent = tmp_path / "sdk"
    pkg = sdk_parent / "qai_hub_apps_utils"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "helper.py").write_text(
        "from qai_hub_apps_utils.math_utils import add\n"
        "def do_something(): return add(1, 2)\n"
    )
    (pkg / "math_utils.py").write_text("def add(a, b): return a + b\n")
    (pkg / "unreferenced.py").write_text("# never reference this\n")
    req_dir = pkg / "requirements"
    req_dir.mkdir()
    (req_dir / "requirements-helper.txt").write_text("numpy>=1.24\n")
    (req_dir / "requirements-math_utils.txt").write_text("# no extra deps\n")
    return sdk_parent
