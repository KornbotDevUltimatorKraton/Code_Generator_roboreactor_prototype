#!/usr/bin/env python3
"""
CLI tool to upload firmware to STM32Duino boards using Arduino CLI and dfu-util.
"""
import argparse
import subprocess
import sys
import os

def run_command(cmd, check=True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="STM32Duino Firmware Uploader")
    parser.add_argument('--board', required=True, help='STM32Duino board FQBN (e.g. stm32:stm32:genericSTM32F103C8)')
    parser.add_argument('--port', required=False, help='Serial port (if needed)')
    parser.add_argument('--sketch', required=True, help='Path to Arduino sketch or .ino file')
    parser.add_argument('--build-dir', default='build', help='Build directory')
    parser.add_argument('--dfu', action='store_true', help='Use dfu-util for upload')
    args = parser.parse_args()

    # Compile the sketch
    build_cmd = [
        'arduino-cli', 'compile', '--fqbn', args.board, '--output-dir', args.build_dir, args.sketch
    ]
    run_command(build_cmd)

    # Find the .bin file
    bin_files = [f for f in os.listdir(args.build_dir) if f.endswith('.bin')]
    if not bin_files:
        print('No .bin file found after compilation.', file=sys.stderr)
        sys.exit(1)
    bin_path = os.path.join(args.build_dir, bin_files[0])
    print(f"Firmware binary: {bin_path}")

    if args.dfu:
        # Upload using dfu-util
        dfu_cmd = [
            'dfu-util', '-a', '0', '-d', '0483:df11', '-s', '0x08000000:leave', '-D', bin_path
        ]
        run_command(dfu_cmd)
    else:
        # Upload using Arduino CLI (serial/bootloader)
        upload_cmd = [
            'arduino-cli', 'upload', '-p', args.port if args.port else '', '--fqbn', args.board, args.sketch
        ]
        # Remove empty port argument if not provided
        upload_cmd = [arg for arg in upload_cmd if arg]
        run_command(upload_cmd)

if __name__ == '__main__':
    main()
