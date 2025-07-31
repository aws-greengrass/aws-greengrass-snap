#!/bin/bash

# Simple script to build the AWS IoT Greengrass V2 snap
set -e

echo "Building AWS IoT Greengrass V2 snap package"

# Clean up previous build artifacts
echo "Cleaning up previous builds..."
rm -rf parts prime stage

# Build the snap
echo "Building snap package..."
snapcraft --destructive-mode

echo "Build completed."