#!/bin/bash

# Add logging
echo "$(date): Greengrass daemon starting..." 
echo "SNAP_DATA: $SNAP_DATA"
echo "SNAP_COMMON: $SNAP_COMMON"
echo "SNAP: $SNAP"

# Wait for system to fully boot
sleep 30

# Use SNAP_COMMON for Greengrass location
GREENGRASS_DIR="$SNAP_COMMON/greengrass/v2"
echo "Looking for Greengrass at: $GREENGRASS_DIR"

if [ ! -d "$GREENGRASS_DIR" ]; then
    echo "Greengrass not configured yet. Waiting..."
    while [ ! -d "$GREENGRASS_DIR" ]; do
        echo "Still waiting for Greengrass configuration at $GREENGRASS_DIR..."
        sleep 60
    done
fi

echo "Found Greengrass directory, attempting to start..."

# Use the Java binary from within the snap
JAVA_BIN="$SNAP/usr/lib/jvm/java-11-openjdk-arm64/bin/java"
echo "Using Java binary: $JAVA_BIN"

# Check if Java binary exists
if [ ! -f "$JAVA_BIN" ]; then
    echo "ERROR: Java binary not found at $JAVA_BIN"
    # Try to find Java in common locations within the snap
    find "$SNAP" -name "java" -type f 2>/dev/null || echo "No Java binary found in snap"
    exit 1
fi

# Check if Greengrass JAR exists
JAR_FILE="$GREENGRASS_DIR/lib/Greengrass.jar"
if [ ! -f "$JAR_FILE" ]; then
    echo "ERROR: Greengrass.jar not found at $JAR_FILE"
    ls -la "$GREENGRASS_DIR/lib/" || echo "lib directory not found"
    exit 1
fi

# Start Greengrass with the snap's Java binary
cd "$GREENGRASS_DIR"
echo "Starting Greengrass from directory: $(pwd)"

# Use the configuration file if available
CONFIG_FILE="$GREENGRASS_DIR/config/effectiveConfig.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo "Using config file: $CONFIG_FILE"
    exec "$JAVA_BIN" -Droot="$GREENGRASS_DIR" -Dlog.store=FILE \
         -jar "$JAR_FILE" \
         --config "$CONFIG_FILE"
else
    echo "Config file not found, starting with basic parameters"
    exec "$JAVA_BIN" -Droot="$GREENGRASS_DIR" -Dlog.store=FILE \
         -jar "$JAR_FILE"
fi

