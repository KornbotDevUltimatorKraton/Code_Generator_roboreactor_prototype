#!/bin/bash
# Installation script for STM32Duino CLI uploader dependencies
set -e

# Update package list
sudo apt-get update

# Install Arduino CLI
if ! command -v arduino-cli &> /dev/null; then
    echo "Installing Arduino CLI..."
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
    sudo mv bin/arduino-cli /usr/local/bin/
    rm -rf bin
else
    echo "Arduino CLI already installed."
fi

# Install dfu-util
if ! command -v dfu-util &> /dev/null; then
    echo "Installing dfu-util..."
    sudo apt-get install -y dfu-util
else
    echo "dfu-util already installed."
fi

echo "All tools installed successfully."
