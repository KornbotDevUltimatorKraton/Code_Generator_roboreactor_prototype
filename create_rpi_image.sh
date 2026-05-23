#!/bin/bash
# Script to create a Raspberry Pi image from existing boot and rootfs directories
# Usage: sudo bash create_rpi_image.sh

set -e

# CONFIGURABLE VARIABLES
BOOT_DIR="./boot"      # Path to your boot directory
ROOTFS_DIR="./rootfs"  # Path to your rootfs directory
IMAGE_NAME="rpi_clone.img"
IMAGE_SIZE="4G"        # Adjust size as needed

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

# Create empty image
fallocate -l $IMAGE_SIZE $IMAGE_NAME

# Partition the image: 256MB boot (FAT32), rest root (ext4)
echo -e "o\nn\np\n1\n\n+256M\nt\nc\nn\np\n2\n\n\nw" | fdisk $IMAGE_NAME

# Set up loop devices
LOOPDEV=$(losetup --show -fP $IMAGE_NAME)

# Format partitions
mkfs.vfat ${LOOPDEV}p1
mkfs.ext4 ${LOOPDEV}p2

# Mount partitions
mkdir -p /mnt/rpi_boot /mnt/rpi_root
mount ${LOOPDEV}p1 /mnt/rpi_boot
mount ${LOOPDEV}p2 /mnt/rpi_root

# Copy files
echo "Copying boot files..."
cp -a $BOOT_DIR/* /mnt/rpi_boot/
echo "Copying rootfs files..."
cp -a $ROOTFS_DIR/* /mnt/rpi_root/

# Sync and cleanup
sync
umount /mnt/rpi_boot
umount /mnt/rpi_root
losetup -d $LOOPDEV
rm -rf /mnt/rpi_boot /mnt/rpi_root

echo "Image $IMAGE_NAME created successfully."
