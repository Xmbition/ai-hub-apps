# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tap import Tap

from qai_hub_apps_test.configs.asset_bases_yaml import AssetBases
from qai_hub_apps_test.configs.info_yaml import AppStatus, QAIHAAppInfo
from qai_hub_apps_test.configs.registry_yaml import AppRegistry
from qai_hub_apps_test.utils.paths import get_all_apps


class GenerateRegistryParser(Tap):
    output_dir: Path  # Directory where registry.yaml will be written
    schema_version: str = "1.0"  # Schema version to embed in the registry
    min_cli_version: str = "0.0.1"  # Minimum CLI version required to use this registry
    ref: str = "main"  # Git ref (branch or tag) used to construct GitHub URLs


def _resolve_repo_url(info: QAIHAAppInfo, repo_base: str, ref: str) -> str:
    """Return the full GitHub URL for an app's source.

    Uses app_repo_url directly if set (e.g. external repos); otherwise
    constructs the URL from repo_base, ref, and app_repo_relative_path.
    """
    if info.app_repo_url:
        return info.app_repo_url
    return f"{repo_base}/tree/{ref}/apps/{info.app_repo_relative_path}"


def main() -> None:
    args = GenerateRegistryParser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    repo_base = AssetBases.load().app_repo_base
    print(f"Using ref '{args.ref}' for GitHub URLs (repo base: {repo_base})")

    public_apps: list[QAIHAAppInfo] = []
    for rel_path in get_all_apps():
        info, _ = QAIHAAppInfo.from_app(rel_path)
        if info.status == AppStatus.PUBLISHED:
            resolved_url = _resolve_repo_url(info, repo_base, args.ref)
            public_apps.append(info.model_copy(update={"app_repo_url": resolved_url}))

    ids = [a.id for a in public_apps]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise SystemExit(f"Error: duplicate app IDs found: {sorted(dupes)}")

    registry = AppRegistry(
        schema_version=args.schema_version,
        min_cli_version=args.min_cli_version,
        generated_at=datetime.utcnow(),
        apps=public_apps,
    )
    registry.to_yaml(args.output_dir / "registry.yaml", write_if_empty=True)
    print(
        f"Wrote {len(public_apps)} public app(s) to {args.output_dir / 'registry.yaml'}"
    )


if __name__ == "__main__":
    main()
