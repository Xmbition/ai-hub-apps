# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
import argparse
import sys
from pathlib import Path

from qai_hub_apps import __version__
from qai_hub_apps.commands.list_apps import run_info, run_list
from qai_hub_apps.registry import Registry


def main() -> None:
    epilog = (
        "Examples:\n"
        "  qai-hub-apps list                   List all available apps\n"
        "  qai-hub-apps info <app_id>          Show details for an app\n"
    )
    parser = argparse.ArgumentParser(
        prog="qai-hub-apps",
        description="CLI for managing and deploying Qualcomm® AI Hub Apps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command")

    def add_registry_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--registry",
            type=Path,
            default=None,
            help="Path to registry.yaml (defaults to bundled registry)",
        )

    list_parser = subparsers.add_parser("list", help="List available apps")
    add_registry_arg(list_parser)

    info_parser = subparsers.add_parser("info", help="Show details for an app")
    info_parser.add_argument("app_id", help="App ID (from 'qai-hub-apps list')")
    add_registry_arg(info_parser)

    args = parser.parse_args()

    registry = getattr(args, "registry", None)
    registry_path = registry or Path(__file__).parent / "registry.yaml"

    if args.command not in (None, "list", "info"):
        parser.print_help()
        sys.exit(1)

    if not registry_path.exists():
        print(f"Registry not found: {registry_path}")
        print("Tip: pass --registry PATH")
        sys.exit(1)

    registry = Registry.load(registry_path)

    if args.command is None:
        parser.print_help()
    elif args.command == "list":
        run_list(registry)
    elif args.command == "info":
        run_info(args.app_id, registry)


if __name__ == "__main__":
    main()
