# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
import argparse

from qai_hub_apps import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="qai-hub-apps",
        description="CLI for managing and deploying Qualcomm® AI Hub Apps.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
