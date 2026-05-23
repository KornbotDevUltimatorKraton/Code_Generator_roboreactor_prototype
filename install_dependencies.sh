#!/bin/bash
echo "Starting Installation..."
echo "Updating system and installing base dependencies..."
sudo apt-get update
sudo apt-get install -y curl git build-essential python3 python3-pip python3-venv python3-opencv

echo "Detecting System Specifications..."
# Detect Memory
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
echo "Total Memory: ${TOTAL_MEM} MB"

# Detect Python Version and verify compatibility (Ultralytics requires Python >= 3.8)
echo "Checking Python Version Compatibility..."
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed on this system."
    exit 1
fi
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
echo "Detected Python: ${PYTHON_MAJOR}.${PYTHON_MINOR}"
if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 8 ]; then
    echo "Error: Python 3.8 or higher is required to run the generated middleware libraries (ultralytics/YOLOv8)."
    echo "Please upgrade your Python installation and try again."
    exit 1
fi

# Detect SBC or Laptop
IS_SBC=0
if [ -f /sys/firmware/devicetree/base/model ]; then
    MODEL=$(tr -d '\0' < /sys/firmware/devicetree/base/model)
    echo "Detected SBC Model: $MODEL"
    IS_SBC=1
else
    echo "Generic PC/Laptop detected."
fi

# CPU Architecture
ARCH=$(uname -m)
echo "Architecture: $ARCH"

# Installing/Updating Rust Language Compiler
echo "Checking Rust Compiler..."
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

# Verify Rust compiler setup and fallback if needed
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

# Detect memory requirements specifically before Ollama installation
echo "Checking memory requirements for Ollama..."
if [ -n "$TOTAL_MEM" ] && [ "$TOTAL_MEM" -eq "$TOTAL_MEM" ] 2>/dev/null; then
    if [ "$TOTAL_MEM" -lt 4000 ]; then
        echo "Warning: System memory is ${TOTAL_MEM} MB (less than 4GB)."
        echo "Ollama and its LLM models run best with at least 4GB of RAM."
        echo "Proceeding with Ollama installation, but performance may be slow or unstable."
    else
        echo "Memory check passed: ${TOTAL_MEM} MB is sufficient for Ollama."
    fi
else
    echo "Warning: Could not determine total memory accurately. Proceeding anyway."
fi

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sudo sh

echo "Creating Python Virtual Environment (venv)..."
# Create venv at the project root directory (one level up from Installer folder)
python3 -m venv "$(dirname "$0")/../venv"

# Create a custom temporary directory for pip to avoid running out of space in /tmp (common on SBCs)
PIP_TMP_DIR="$(dirname "$0")/../pip_tmp"
mkdir -p "$PIP_TMP_DIR"
export TMPDIR="$PIP_TMP_DIR"

echo "Upgrading pip inside virtual environment..."
"$(dirname "$0")/../venv/bin/pip" install --upgrade pip

echo "Installing YOLOv8 (ultralytics), OpenCV, FastAPI, and Uvicorn inside virtual environment..."
"$(dirname "$0")/../venv/bin/pip" install ultralytics opencv-python fastapi uvicorn

# Clean up custom pip temp dir
rm -rf "$PIP_TMP_DIR"
unset TMPDIR

echo "Creating startup runner script (run.sh)..."
RUN_SCRIPT_PATH="$(dirname "$0")/../run.sh"
cat << 'EOF' > "$RUN_SCRIPT_PATH"
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ ! -d "${SCRIPT_DIR}/venv" ]; then
    echo "Error: Virtual environment (venv) directory not found at ${SCRIPT_DIR}/venv."
    echo "Please run the Installer/install_dependencies.sh script first."
    exit 1
fi
echo "Activating virtual environment and starting middleware..."
source "${SCRIPT_DIR}/venv/bin/activate"
python3 "${SCRIPT_DIR}/middleware/middleware.py"
EOF
chmod +x "$RUN_SCRIPT_PATH"
echo "Runner script created at: $RUN_SCRIPT_PATH"

echo "Installation complete!"
echo "To run your middleware within the virtual environment, execute:"
echo "  python3 \"$(dirname "$0")/../middleware/middleware.py\" using the virtual env python:"
echo "  \"$(dirname "$0")/../venv/bin/python3\" \"$(dirname "$0")/../middleware/middleware.py\""
echo "Or run the startup script directly:"
echo "  \"$(dirname "$0")/../run.sh\""
