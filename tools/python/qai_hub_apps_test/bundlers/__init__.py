# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from qai_hub_apps_test.bundlers.python.bundle import bundle_source as _bundle_source
from qai_hub_apps_test.bundlers.shell.bundle import bundle_scripts as _bundle_scripts
from qai_hub_apps_test.configs.info_yaml import AppLanguage, QAIHAAppInfo
from qai_hub_apps_test.utils.paths import find_app_dir


def bundle_app(
    app: str | Path,
    output_dir: Path,
    sdk_parent: Path | None = None,
    shared_scripts_root: Path | None = None,
    make_zip: bool = False,
) -> None:
    """Bundle an app by app ID or directory path.

    Orchestrates three steps inside a temporary directory:
    1. **bundle_source** — copies app source, shared SDK modules, and merged
       ``requirements.txt`` (Python bundler).
    2. **bundle_scripts** — detects ``install_*.sh`` / ``install_*.ps1`` in the
       bundle, copies referenced shared scripts to ``scripts/``, copy versions.env and rewrites source/dot-source lines.
    3. **Finalize** — copies the staging directory to ``output_dir/<app_id>/``
       or zips it to ``output_dir/<app_id>.zip``.

    Parameters
    ----------
    app:
        Either a string app ID (resolved via find_app_dir) or a Path to
        the app's root directory.
    output_dir:
        Directory where the bundle will be written.
    sdk_parent:
        Path to the directory containing ``qai_hub_apps_utils``. Auto-resolved
        from the repository structure if None.
    shared_scripts_root:
        Path to the shared shell scripts directory (``apps/_shared/scripts/``).
        Auto-resolved from the repository structure if None.
    make_zip:
        If True, produce a zip archive; otherwise copy to a subdirectory.

    Raises
    ------
    NotImplementedError
        If the app does not include Python in its languages.
    """
    app_dir: Path = find_app_dir(app) if isinstance(app, str) else app
    app_info, _ = QAIHAAppInfo.from_app(app_dir)

    if AppLanguage.PYTHON not in app_info.languages:
        raise NotImplementedError(
            f"App '{app_info.id}' does not support Python bundling "
            f"(languages={[lang.value for lang in app_info.languages]}). "
            "Only Python apps can be bundled at this time."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as _tmp:
        tmp_dir = Path(_tmp) / app_info.id

        _bundle_source(app_dir, tmp_dir, sdk_parent)

        _bundle_scripts(tmp_dir, shared_scripts_root)

        if make_zip:
            zip_path = output_dir / f"{app_info.id}.zip"
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(tmp_dir.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(tmp_dir))
            print(f"Bundle written to: {zip_path}")
        else:
            dest = output_dir / app_info.id
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(tmp_dir, dest)
            print(f"Bundle written to: {dest}")
