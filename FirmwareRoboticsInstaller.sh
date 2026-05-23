# --- System and Python base dependencies (from install_dependencies.sh) ---
sudo apt-get update
sudo apt-get install -y curl git build-essential python3 python3-pip python3-venv

# Optional: install OpenCV via apt for some platforms
sudo apt-get install -y python3-opencv

# --- Memory and Python version check (from install_dependencies.sh) ---
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
echo "Total Memory: ${TOTAL_MEM} MB"
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed on this system."
    exit 1
fi
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
echo "Detected Python: ${PYTHON_MAJOR}.${PYTHON_MINOR}"
if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 8 ]; then
    echo "Error: Python 3.8 or higher is required for Ultralytics/YOLOv8."
    exit 1
fi

# --- Rust compiler install/update (from install_dependencies.sh) ---
if command -v rustc &> /dev/null; then
    echo "Rust is already installed. Checking for updates..."
    if command -v rustup &> /dev/null; then
        rustup update stable
    else
        echo "rustup not found. Attempting to update rustc and cargo via apt..."
        sudo apt-get install -y --only-upgrade rustc cargo
    fi
else
    echo "Rust is not installed. Installing Rust via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
fi
if command -v rustc &> /dev/null; then
    echo "Rust compiler verified successfully:"
    rustc --version
    cargo --version
else
    echo "rustup environment not loaded. Attempting fallback installation via apt..."
    sudo apt-get install -y rustc cargo
    if command -v rustc &> /dev/null; then
        echo "Rust compiler installed via apt:"
        rustc --version
    else
        echo "Warning: Rust compiler could not be set up. Some libraries requiring Rust compilation might fail to install."
    fi
fi

# --- Remove EXTERNAL-MANAGED to allow pip installs without ---
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_LIB_DIR="/usr/lib/python${PYTHON_VERSION}"
EXTERNAL_MANAGED_FILE="${PYTHON_LIB_DIR}/EXTERNAL-MANAGED"
if [ -f "$EXTERNAL_MANAGED_FILE" ]; then
    echo "Removing $EXTERNAL_MANAGED_FILE to allow pip installs..."
    sudo rm -f "$EXTERNAL_MANAGED_FILE"
    echo "EXTERNAL-MANAGED removed."
else
    echo "EXTERNAL-MANAGED file not found in $PYTHON_LIB_DIR."
fi

# --- Ensure python3-pip is installed ---
if ! command -v pip3 &> /dev/null; then
    echo "python3-pip not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-pip[Unit]
Description=YOLOv8 Realtime Object Detection Service
After=network.target

[Service]
Type=simple
User=roboreactor
WorkingDirectory=/home/roboreactor

# Run directly from the virtual environment
ExecStart=/home/roboreactor/.venv_yolov8/bin/python /home/roboreactor/yolov8_realtime.py

Restart=always
RestartSec=5

# Logs
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
else
    echo "python3-pip is already installed."
fi

# --- YOLOv8/Ultralytics install (from install_dependencies.sh) ---
sudo pip3 install ultralytics
# Install OpenCV for Python (generic and ARM)
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"
if [[ "$ARCH" == "x86_64" ]]; then
    echo "Installing OpenCV for x86_64 (generic PC)"
    sudo pip3 install opencv-python opencv-contrib-python
elif [[ "$ARCH" == "aarch64" || "$ARCH" == arm* ]]; then
    echo "Installing OpenCV for ARM (Raspberry Pi, Jetson, etc.)"
    sudo pip3 install opencv-python opencv-contrib-python
else
    echo "Unknown architecture, attempting generic OpenCV install"
    sudo pip3 install opencv-python opencv-contrib-python
fi

# --- Add speech recognition dependencies ---
echo "Installing faster-whisper and sounddevice for speech recognition..."
sudo pip3 install faster-whisper sounddevice numpy
echo "Installing Vosk and dependencies for speech recognition..."
sudo pip3 install vosk srt requests

# --- Download Vosk English and Chinese models ---
cd /home/kornbotdev/Robotic_control_networking || exit 1
if [ ! -d "vosk-model-en-us-0.22" ]; then
    echo "Downloading Vosk English model..."
    wget -O vosk-model-en-us.zip https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
    unzip vosk-model-en-us.zip
    rm vosk-model-en-us.zip
fi
if [ ! -d "vosk-model-cn/vosk-model-small-cn-0.22" ]; then
    echo "Downloading Vosk Chinese model..."
    mkdir -p vosk-model-cn
    wget -O vosk-model-cn.zip https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
    unzip vosk-model-cn.zip -d vosk-model-cn
    rm vosk-model-cn.zip
fi
cd -

#!/bin/bash
# Robotics Firmware Installer Script
# Refined for robotics, includes camera, Ollama, and essential robotics libraries

echo "Welcome to the Robotics Firmware Installer"

set -e

# Update and upgrade system
sudo apt-get update && sudo apt-get upgrade -y

# Set debconf to interactive/critical
sudo dpkg-reconfigure debconf


# Essential build tools and Python
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-setuptools python3-pip python3-venv cmake git python3-tk scrot openssh-server htop snapd arduino


# Firewall and nginx setup
sudo apt-get install ufw -y
sudo ufw enable
sudo ufw status
sudo ufw allow 80
sudo ufw allow 8000
sudo ufw allow 8095
sudo ufw allow 443
sudo ufw allow 25
sudo ufw allow 21
sudo ufw allow 21
sudo ufw allow 587
sudo ufw allow ssh
echo "Install nginx"
sudo apt-get install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
sudo ufw allow 'Nginx Full'
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
sudo ufw status


# Camera and robotics-specific packages
sudo apt-get install -y python3-picamera2 i2c-tools python3-pyaudio

# Python sensor and robotics libraries
sudo pip3 install virtualenv i2csense smbus smbus2 Adafruit-Blinka bmp280 pyinstaller adafruit-circuitpython-mpu6050 adafruit-circuitpython-icm20x imutils unidecode streamlit Pynsq python3-scapy

# Additional libraries from FirmwareNongpuserver.sh
sudo apt install -y python3-sphinx
sudo pip3 install fastapi
sudo pip3 install scipy
sudo pip3 install sklearn
sudo pip3 install tpot
sudo pip3 install matplotlib --upgrade
sudo pip3 install geonamescache
sudo pip3 install pandas
sudo apt-get install -y python3-zbar
sudo pip3 install Pillow
sudo pip3 install PyPDF2
sudo pip3 install fpdf2
sudo pip3 install pdfquery
sudo pip3 install PyMuPDF
sudo pip3 install wordninja
sudo pip3 install pattern
sudo pip3 install openpyxl
sudo pip3 install gensim
sudo pip3 install jinja2
sudo pip3 install camelot-py[cv]
sudo pip3 install imgextract
sudo pip3 install cython
sudo pip3 install pcb-tools-extension
sudo pip3 install GlobalPayments.Api
sudo pip install tika --upgrade
sudo pip3 install jiwer
sudo pip3 install geopy
sudo pip3 install SpeechRecognition
sudo pip3 install pygltflib
sudo apt-get install -y bluetooth libbluetooth-dev
sudo pip3 install pybluez
sudo pip3 install nltk --upgrade
sudo apt-get install -y libbluetooth-dev
echo "Mail sender"
sudo pip3 install secure-smtplib
echo "Installing the serial communication function"
sudo pip3 install pyserial
sudo pip3 install pyfirmata
sudo pip3 uninstall regex -y
sudo pip3 install regex
sudo apt-get install -y python3-scapy
sudo pip3 install scapy
echo "Install tensorflow for the deep learning and machine learning capability"
sudo pip3 install numpy
sudo pip3 install trimesh
sudo pip3 install protobuf
sudo pip3 install googlesearch-python
sudo apt-get install -y dnsutils

# GPU checker
sudo apt install -y mesa-utils

# Ollama Python and Ollama system install
sudo pip3 install ollama

# Install curl if not present
sudo apt-get install -y curl

# Download and install Ollama (system)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama system binary..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama is already installed."
fi

echo "Robotics firmware installation complete!"
