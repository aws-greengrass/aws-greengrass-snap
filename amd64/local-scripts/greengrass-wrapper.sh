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
JAVA_BIN="$SNAP/usr/lib/jvm/java-11-openjdk-amd64/bin/java"
echo "Using Java binary: $JAVA_BIN"

# Check if Java binary exists
if [ ! -f "$JAVA_BIN" ]; then
    echo "ERROR: Java binary not found at $JAVA_BIN"
    # Try to find Java in common locations within the snap
    find "$SNAP" -name "java" -type f 2>/dev/null || echo "No Java binary found in snap"
    exit 1
fi

# Check if Greengrass JAR exists (try both locations)
JAR_FILE="$GREENGRASS_DIR/alts/current/distro/lib/Greengrass.jar"
if [ ! -f "$JAR_FILE" ]; then
    JAR_FILE="$GREENGRASS_DIR/lib/Greengrass.jar"
    if [ ! -f "$JAR_FILE" ]; then
        echo "ERROR: Greengrass.jar not found"
        ls -la "$GREENGRASS_DIR/lib/" 2>/dev/null || echo "lib directory not found"
        ls -la "$GREENGRASS_DIR/alts/current/distro/lib/" 2>/dev/null || echo "distro lib directory not found"
        exit 1
    fi
fi
echo "Using JAR: $JAR_FILE"

# Start Greengrass with the snap's Java binary
cd "$GREENGRASS_DIR"
echo "Starting Greengrass from directory: $(pwd)"
echo "Command: $JAVA_BIN -Droot=$GREENGRASS_DIR -Dlog.store=FILE -jar $JAR_FILE"

exec "$JAVA_BIN" -Droot="$GREENGRASS_DIR" -Dlog.store=FILE -jar "$JAR_FILE"

