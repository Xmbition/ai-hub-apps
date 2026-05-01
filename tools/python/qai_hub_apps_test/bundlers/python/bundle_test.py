# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

from pathlib import Path

import pytest

from qai_hub_apps_test.bundlers.python.bundle import bundle_source
from qai_hub_apps_test.configs.info_yaml import AppLanguage
from qai_hub_apps_test.conftest import make_sample_app_info

pytestmark = pytest.mark.bundler_unit

_SDK = "qai_hub_apps_utils"


def test_non_python_app_exits(tmp_path: Path) -> None:
    app_dir = tmp_path / "myapp"
    app_dir.mkdir()
    make_sample_app_info(id="myapp", languages=[AppLanguage.CPP]).to_yaml(
        app_dir / "info.yaml", write_if_empty=True
    )
    sdk = tmp_path / "sdk"
    (sdk / _SDK).mkdir(parents=True)
    (sdk / _SDK / "__init__.py").write_text("")
    with pytest.raises(ValueError, match="not a Python app"):
        bundle_source(app_dir, tmp_path / "out", sdk)


def test_bundle_source_creates_output_dir(
    dummy_python_app_path: Path, dummy_python_sdk_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    bundle_source(dummy_python_app_path, out / "my_dummy_app", dummy_python_sdk_path)
    assert (out / "my_dummy_app").is_dir()


def test_bundle_source_copies_app_files(
    dummy_python_app_path: Path, dummy_python_sdk_path: Path, tmp_path: Path
) -> None:
    out_dir = tmp_path / "bundle_out"
    bundle_source(dummy_python_app_path, out_dir, dummy_python_sdk_path)
    assert (out_dir / "main.py").exists()


def test_bundle_source_writes_requirements_txt(
    dummy_python_app_path: Path, dummy_python_sdk_path: Path, tmp_path: Path
) -> None:
    out_dir = tmp_path / "bundle_out"
    bundle_source(dummy_python_app_path, out_dir, dummy_python_sdk_path)
    reqs = (out_dir / "requirements.txt").read_text()
    assert "Pillow>=9.0" in reqs


def test_bundle_source_no_sdk_imports_no_sdk_dir(tmp_path: Path) -> None:
    app_dir = tmp_path / "myapp"
    app_dir.mkdir()
    make_sample_app_info(id="myapp").to_yaml(app_dir / "info.yaml", write_if_empty=True)
    (app_dir / "main.py").write_text("import os\n")
    sdk = tmp_path / "sdk"
    (sdk / _SDK).mkdir(parents=True)
    (sdk / _SDK / "__init__.py").write_text("")
    out_dir = tmp_path / "out" / "myapp"
    bundle_source(app_dir, out_dir, sdk)
    assert not (out_dir / _SDK).exists()


def test_bundle_source_with_sdk_import_copies_sdk_file(
    dummy_python_app_path: Path, dummy_python_sdk_path: Path, tmp_path: Path
) -> None:
    out_dir = tmp_path / "bundle_out"
    bundle_source(dummy_python_app_path, out_dir, dummy_python_sdk_path)
    assert (out_dir / _SDK / "helper.py").exists()
