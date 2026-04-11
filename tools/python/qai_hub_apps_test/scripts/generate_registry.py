# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from tap import Tap

from qai_hub_apps_test.bundlers import Bundler
from qai_hub_apps_test.bundlers import python as python_bundler
from qai_hub_apps_test.configs.asset_bases_yaml import AssetBases
from qai_hub_apps_test.configs.info_yaml import (
    AppLanguage,
    AppStatus,
    AppUrl,
    QAIHAAppInfo,
)
from qai_hub_apps_test.configs.registry_yaml import AppRegistry
from qai_hub_apps_test.utils.aws import (
    QAIHM_PUBLIC_S3_BUCKET,
    attempt_with_s3_credentials_warning,
    get_qaihm_s3,
)
from qai_hub_apps_test.utils.paths import REPOSITORY_ROOT, get_all_apps


def _read_cli_version() -> str:
    from setuptools_scm import get_version

    return get_version(root=str(REPOSITORY_ROOT))


class GenerateRegistryParser(Tap):
    output_dir: Path  # Directory where registry.yaml will be written
    schema_version: str = "1.0"  # Schema version to embed in the registry
    min_cli_version: str = "0.0.1"  # Minimum CLI version required to use this registry
    ref: str = "main"  # Git ref (branch or tag) used to construct GitHub URLs

    cli_version: str = _read_cli_version()  # CLI version used for zip path / S3 path
    upload: bool = False  # Upload zips to S3 (default: write locally)
    zips_dir: Path | None = (
        None  # Local zip output dir (default: output_dir/zips); only used when not uploading
    )


def _resolve_repo_url(info: QAIHAAppInfo, repo_base: str, ref: str) -> str:
    """Return the full GitHub URL for an app's source.

    Uses app_repo_url directly if set (e.g. external repos); otherwise
    constructs the URL from repo_base, ref, and app_repo_relative_path.
    """
    if info.app_repo_url:
        return info.app_repo_url
    return f"{repo_base}/tree/{ref}/apps/{info.app_repo_relative_path}"


def build_app(
    app_dir: Path,
    output_dir: Path,
    sdk_parent: Path,
    bundler: Bundler,
) -> Path:
    """Bundle an app into a zip in output_dir. Returns the zip path."""
    bundler(app_dir, output_dir, sdk_parent, make_zip=True)
    return output_dir / f"{app_dir.name}.zip"


def upload_app(
    zip_path: Path, app_id: str, bucket: Any, s3_prefix: str, cli_version: str
) -> None:
    """Upload an app zip to S3."""
    s3_key = f"{s3_prefix}/{cli_version}/{app_id}/source.zip"

    def _upload(key: str = s3_key, path: Path = zip_path) -> None:
        bucket.upload_file(str(path), key, ExtraArgs={"ACL": "public-read"})

    attempt_with_s3_credentials_warning(_upload)
    print(f"Uploaded to s3://{QAIHM_PUBLIC_S3_BUCKET}/{s3_key}")


def main() -> None:
    args = GenerateRegistryParser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    repo_base = AssetBases.load().app_repo_base
    print(f"Using ref '{args.ref}' for GitHub URLs (repo base: {repo_base})")

    public_apps: list[tuple[QAIHAAppInfo, Path]] = []
    for rel_path in get_all_apps():
        info, app_dir = QAIHAAppInfo.from_app(rel_path)
        if info.id != app_dir.name:
            raise SystemExit(
                f"Error: app ID '{info.id}' in {app_dir / 'info.yaml'} "
                f"does not match directory name '{app_dir.name}'."
            )
        if info.status == AppStatus.PUBLISHED:
            resolved_url = _resolve_repo_url(info, repo_base, args.ref)
            public_apps.append(
                (info.model_copy(update={"app_repo_url": resolved_url}), app_dir)
            )

    ids = [info.id for info, _ in public_apps]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise SystemExit(f"Error: duplicate app IDs found: {sorted(dupes)}")

    s3_prefix = "qai-hub-apps/apps"
    S3_REGION = "us-west-2"
    s3_base = f"https://{QAIHM_PUBLIC_S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

    if args.upload:
        if "dev" in args.cli_version:
            print(
                f"\nWarning: version '{args.cli_version}' looks like a development build.\n"
                f"Uploading dev versions to S3 is not recommended."
            )
            answer = input("Continue? [y/N]: ").strip().lower()
            if answer != "y":
                sys.exit("Aborted.")
        bucket, _ = get_qaihm_s3(QAIHM_PUBLIC_S3_BUCKET, requires_admin=False)

    sdk_parent = python_bundler.resolve_sdk_root(None)
    bundled_apps: list[QAIHAAppInfo] = []

    if args.upload:
        context: Any = tempfile.TemporaryDirectory()
    else:
        zips_dir = (args.zips_dir or args.output_dir / "zips") / args.cli_version
        zips_dir.mkdir(parents=True, exist_ok=True)
        context = _NullContext(zips_dir)

    with context as build_dir:
        build_path = Path(build_dir)
        for info, app_dir in public_apps:
            print(f"\n{f' {info.id} ':─^60}")
            if AppLanguage.PYTHON not in info.languages:
                print(
                    f"Skipping: not a Python app "
                    f"(languages={[l.value for l in info.languages]})"
                )
                continue

            if args.upload:
                zip_path = build_app(
                    app_dir, build_path, sdk_parent, python_bundler.bundle
                )
                upload_app(zip_path, info.id, bucket, s3_prefix, args.cli_version)
                source_url = (
                    f"{s3_base}/{s3_prefix}/{args.cli_version}/{info.id}/source.zip"
                )
            else:
                app_zip_dir = build_path / info.id
                app_zip_dir.mkdir(parents=True, exist_ok=True)
                zip_path = build_app(
                    app_dir, app_zip_dir, sdk_parent, python_bundler.bundle
                )
                final_path = app_zip_dir / "source.zip"
                zip_path.rename(final_path)
                source_url = final_path.resolve().as_uri()
                print(f"Saved to {final_path}")

            bundled_apps.append(
                info.model_copy(update={"url": AppUrl(source=source_url)})
            )

    registry = AppRegistry(
        schema_version=args.schema_version,
        min_cli_version=args.min_cli_version,
        version=args.cli_version,
        generated_at=datetime.utcnow(),
        apps=bundled_apps,
    )
    registry.to_yaml(args.output_dir / "registry.yaml", write_if_empty=True)
    print(
        f"\n{'  Summary  ':=^60}"
        f"\nBundled {len(bundled_apps)} app(s) out of {len(public_apps)} public app(s) to {args.output_dir / 'registry.yaml'}"
    )


class _NullContext:
    """Minimal context manager that yields a fixed path (no cleanup)."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def __enter__(self) -> Path:
        return self._path

    def __exit__(self, *_: object) -> None:
        pass


if __name__ == "__main__":
    main()
