# Mediapipe Hand Gesture app

A Python app using GStreamer, OpenCV, and LiteRT that performs hand detection
and gesture analysis on a live camera stream.

## Setup

### 1. Install Python 3.10+

```bash
sudo apt-get update
sudo apt-get install python3 python3-venv
```

### 2. Install Docker

Follow [these instructions](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) to install Docker.

### 3. Install Ubuntu host packages *(skip if not on Ubuntu OS)*

```bash
sudo apt-get install qcom-fastrpc1 qcom-fastrpc-dev
```

If you are using a built-in camera on the Dragonwing RB3, also install `qcom-camera-server`:

```bash
sudo apt-get install qcom-camera-server
```

After installing, reboot the device.

### 4. Create the dev environment

From the repo root, create a virtual environment and install the CLI:

```bash
bash tools/setup_env.sh --with-cli
source qaiha-dev/bin/activate
```

### 5. Fetch the app

```bash
qai-hub-apps fetch mediapipe_hand_gesture_ubuntu_py --model mediapipe_hand_gesture -o <APP_DIR>
cd <APP_DIR>/mediapipe_hand_gesture_ubuntu_py
```

### 6. Build the Docker image

```bash
./build_docker.sh
```

## Running the app

All run commands are issued through `run_docker.sh`.
To list available options:
```
./run_docker.sh --help
```

### List available camera sources

```bash
./run_docker.sh --list-devices
```

### Run with a specific camera

```bash
./run_docker.sh --hexagon-version <HEX_VER> --video-device /dev/video0
```

> [!IMPORTANT]
> You must provide `--hexagon-version` matching your device's Hexagon DSP version. For example, the [Dragonwing RB3 Gen 2](https://www.qualcomm.com/developer/hardware/rb3-gen-2-development-kit) uses Hexagon v68. To find the Hexagon version for your device, visit the [AI Hub device catalogue](https://workbench.aihub.qualcomm.com/devices/).

> [!NOTE]
> To use the integrated camera of a Dragonwing RB3, the `qtiqmmfsrc` GStreamer plugin must be used.
> `./run_docker.sh --hexagon-version v68 --video-gstreamer-source "qtiqmmfsrc name=camsrc camera=0"`.

This serves the camera feed on port 8080. Open a browser and navigate to
`http://<device-ip>:8080` to view the stream.

### Interactive / debug mode

```bash
./run_docker.sh --interactive
```
