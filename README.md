# STM32Duino Firmware Uploader

This project provides tools to compile and upload firmware to STM32Duino boards using Arduino CLI and dfu-util.

## Prerequisites
- Linux (tested on Ubuntu/Debian)
- Internet connection for installation

## Installation

1. **Clone or download this repository**

2. **Install required tools**

```bash
cd /home/kornbotdev/roboreactor_code_generator
chmod +x install_tools.sh
./install_tools.sh
```

This script installs:
- Arduino CLI
- dfu-util

## Usage

### 1. Prepare your Arduino sketch
Place your `.ino` file or sketch folder in a known location.

### 2. Upload firmware

```bash
python3 stm32duino_uploader.py \
  --board stm32:stm32:genericSTM32F103C8 \
  --sketch /path/to/your_sketch.ino \
  --dfu
```

- `--board`: The FQBN for your STM32Duino board (see Arduino CLI documentation).
- `--sketch`: Path to your Arduino sketch or `.ino` file.
- `--dfu`: Use DFU mode for upload (recommended for STM32 boards).
- `--port`: (Optional) Serial port for boards that require it.

### Example

```bash
python3 stm32duino_uploader.py \
  --board stm32:stm32:genericSTM32F103C8 \
  --sketch Blink.ino \
  --dfu
```

## Notes
- Ensure your STM32 board is in DFU mode before uploading (usually by pressing the BOOT0 button and resetting the board).
- The script will compile the sketch and upload the resulting `.bin` file using `dfu-util`.

## License
MIT
