# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import time
import zipfile
from abc import ABC, abstractmethod

from qualcomm_device_cloud_sdk.models import ArtifactType

from qai_hub_apps_test.qdc.qdc_jobs import (
    HUB_DEVICE_TO_QDC_DEVICE_MAP,
    POLL_INTERVAL,
    QDCDevice,
    QDCJobs,
)


def create_zip(zip_path: str, source_dir: str | os.PathLike) -> None:
    """Create a zip archive from source_dir at zip_path."""
    if isinstance(source_dir, os.PathLike):
        source_dir = str(source_dir)

    files_to_zip = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source_dir)
            files_to_zip.append((file_path, arcname))

    # ZIP_STORED (no compression) for speed — files are model bins and source code is few KBs
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
        for file_path, arcname in files_to_zip:
            zf.write(file_path, arcname)


class AppTestArtifactHandler(ABC):
    """Abstract base class for app-test artifact handlers."""

    @abstractmethod
    def create_artifact(
        self,
        curr_dirname: os.PathLike | str,
        app_dir: os.PathLike | str,
        dest_dir: os.PathLike | str,
        run_command: str,
    ) -> str:
        """Create artifact bundle and return path to the zip file."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entry_script(self) -> str | None:
        raise NotImplementedError


class AppTestLinuxArtifactHandler(AppTestArtifactHandler):
    def __init__(self, use_docker: bool = False) -> None:
        self.use_docker = use_docker

    @property
    def entry_script(self) -> str:
        return "/bin/bash /data/local/tmp/TestContent/run_linux.sh"

    def create_artifact(
        self,
        curr_dirname: os.PathLike | str,
        app_dir: os.PathLike | str,
        dest_dir: os.PathLike | str,
        run_command: str,
    ) -> str:
        """Build the test bundle directory and return the path to the zip archive.

        Copies ``run_linux.sh`` and ``ubuntu.dockerfile`` from ``device_scripts/``
        into ``dest_dir``, substituting ``<<RUN_COMMAND>>`` and ``<<USE_DOCKER>>``
        placeholders in the shell script. The app directory is copied in as an
        ``app/`` subdirectory. The whole ``dest_dir`` is then zipped into
        ``test.zip`` one level above it, which is the artifact uploaded to QDC.

        Parameters
        ----------
        curr_dirname
            Directory containing the ``device_scripts/`` folder (typically the
            directory of this source file).
        app_dir
            Directory of the fetched app (output of ``qai-hub-apps fetch``).
        dest_dir
            Staging directory where the bundle contents are assembled.
        run_command
            Shell command to execute on the device inside the app directory;
            substituted into ``run_linux.sh``.

        Returns
        -------
        str
            Absolute path to the created ``test.zip`` archive.
        """
        dest_script = os.path.join(dest_dir, "run_linux.sh")
        shutil.copy(
            os.path.join(curr_dirname, "device_scripts", "run_linux.sh"),
            dest_script,
        )
        with open(dest_script, encoding="utf-8") as f:
            content = f.read()
        with open(dest_script, "w", encoding="utf-8") as f:
            f.write(
                content.replace("<<RUN_COMMAND>>", run_command).replace(
                    "<<USE_DOCKER>>", "true" if self.use_docker else "false"
                )
            )

        shutil.copy(
            os.path.join(curr_dirname, "device_scripts", "ubuntu.dockerfile"),
            dest_dir,
        )

        shutil.copytree(app_dir, os.path.join(dest_dir, "app"))

        zip_path = os.path.join(os.path.dirname(dest_dir), "test.zip")
        create_zip(zip_path, dest_dir)
        return zip_path


class AppTestQDCJobs(QDCJobs):
    """QDC job handler for generic app on-device testing."""

    def _get_artifact_handler(
        self, qdc_device: QDCDevice, use_docker: bool = False
    ) -> AppTestArtifactHandler:
        if qdc_device.iot_platform:
            return AppTestLinuxArtifactHandler(use_docker=use_docker)
        raise NotImplementedError(
            f"On-device app testing is not yet supported for this platform. "
            f"Device: {qdc_device.device.name!r}"
        )

    def add_job_artifacts(
        self,
        qdc_device: QDCDevice,
        app_dir: str | os.PathLike,
        run_command: str,
        use_docker: bool = False,
        save_bundle_dir: str | os.PathLike | None = None,
    ) -> tuple[list[str], str | None]:
        """Prepare and upload app artifacts for job submission.

        Parameters
        ----------
        qdc_device
            QDCDevice instance for the target device.
        app_dir
            Directory of the fetched app (output of ``qai-hub-apps fetch``).
        run_command
            Shell command to execute on the device inside the app directory.
        use_docker
            If True, run the app inside a Docker container on the device.
        save_bundle_dir
            If set, copy the test.zip bundle to this directory before uploading.

        Returns
        -------
        job_artifacts : list[str]
            List of artifact IDs returned by QDC upload.
        entry_script : str | None
            Entry script path used by the test framework.
        """
        curr_dirname = os.path.dirname(os.path.abspath(__file__))
        artifact_handler = self._get_artifact_handler(qdc_device, use_docker)

        with tempfile.TemporaryDirectory() as tmpdirname:
            zip_path = artifact_handler.create_artifact(
                curr_dirname,
                app_dir,
                tmpdirname,
                run_command,
            )
            upload_response = self.upload_file(zip_path, ArtifactType.TESTSCRIPT)
            if save_bundle_dir is not None:
                os.makedirs(save_bundle_dir, exist_ok=True)
                shutil.copy(zip_path, save_bundle_dir)
            if os.path.exists(zip_path):
                os.unlink(zip_path)

        return [upload_response], artifact_handler.entry_script


def submit_app_bundle_to_qdc_device(
    api_token: str,
    device: str,
    app_dir: str | os.PathLike,
    run_command: str,
    job_name: str = "App Test",
    use_docker: bool = False,
    save_bundle_dir: str | os.PathLike | None = None,
) -> bool:
    """Submit a fetched app bundle to QDC for on-device execution.

    Parameters
    ----------
    api_token
        API token for QDC authentication.
    device
        Hub device name to run the job on (must be a key in HUB_DEVICE_TO_QDC_DEVICE_MAP).
    app_dir
        Directory of the fetched app (output of ``qai-hub-apps fetch``).
    run_command
        Shell command to execute on the device inside the app directory.
    job_name
        Name for the QDC job.
    use_docker
        If True, build and run the app inside a Docker container on the device
        using the platform specific ``Dockerfile`` base image.
    save_bundle_dir
        If set, copy the test.zip bundle to this directory before uploading.

    Returns
    -------
    success : bool
        True if the job completed successfully, False otherwise.
    """
    qdc_device = QDCDevice(device)
    app_job = AppTestQDCJobs(
        api_key=api_token,
        app_name_header="AppTestQDCJobApp",
    )

    job_artifacts, entry_script = app_job.add_job_artifacts(
        qdc_device, app_dir, run_command, use_docker, save_bundle_dir
    )

    job_id = app_job.submit_automated_job(
        qdc_device, job_artifacts, entry_script, job_name=job_name
    )
    if job_id is None:
        raise RuntimeError("Job submission failed.")

    print(f"Submitted QDC job with ID: {job_id}")
    job_status = app_job.status(job_id)
    print(f"QDC job {job_id} completed with status: {job_status}")
    app_job.log_upload_status(job_id)
    job_log_files = app_job.get_job_log_files(job_id)
    time.sleep(POLL_INTERVAL)

    if job_log_files:
        with tempfile.TemporaryDirectory() as tmpdirname:
            for job_log in job_log_files:
                target_path = os.path.join(
                    tmpdirname, "logs", f"{job_log.filename}.zip"
                )
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                app_job.download_job_log_files(job_log.filename, target_path)
                print(f"Downloaded log: {job_log.filename}")

    return job_status == "Completed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Submit a fetched app bundle to QDC for on-device testing."
    )
    parser.add_argument(
        "--api-token",
        type=str,
        required=True,
        help="API token for QDC authentication.",
    )
    parser.add_argument(
        "--device",
        type=str,
        required=True,
        choices=HUB_DEVICE_TO_QDC_DEVICE_MAP.keys(),
        help="Hub device name to run the job on.",
    )
    parser.add_argument(
        "--app-dir",
        type=str,
        required=True,
        help="Directory of the fetched app (output of 'qai-hub-apps fetch').",
    )
    parser.add_argument(
        "--run-command",
        type=str,
        required=True,
        help="Shell command to execute on the device inside the app directory.",
    )
    parser.add_argument(
        "--job-name",
        type=str,
        default="App Test",
        help="QDC job name.",
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        default=False,
        help=(
            "Run the app inside a Docker container on the device using the "
            "bundled ubuntu.dockerfile base image."
        ),
    )
    parser.add_argument(
        "--save-bundle",
        type=str,
        default=None,
        metavar="DIR",
        help="If set, copy the test.zip bundle to this directory before uploading.",
    )

    args = parser.parse_args()
    if not os.path.isdir(args.app_dir):
        raise NotADirectoryError(
            f"app-dir '{args.app_dir}' does not exist or is not a directory."
        )
    success = submit_app_bundle_to_qdc_device(
        args.api_token,
        args.device,
        args.app_dir,
        args.run_command,
        args.job_name,
        args.docker,
        args.save_bundle,
    )
    raise SystemExit(0 if success else 1)
