#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script is necessary because loader script needs to be executed from
# $SNAP_DATA/greengrass/v2/alts/current/distro/bin path.
# Referencing this path from the snapcraft.yaml file results in path does not exist errors

set -o xtrace

GREENGRASS_CONFIG="$(snapctl get greengrass-config)"

if [ ! -e "$SNAP_DATA/docker/" ]; then
    mkdir -p "$SNAP_DATA/docker"
fi

export DOCKER_CONFIG="$SNAP_DATA/docker"
export DOCKER_ENV="$SNAP/docker-env"
export PATH="$DOCKER_ENV/usr/sbin:$DOCKER_ENV/usr/bin:$DOCKER_ENV/sbin:$DOCKER_ENV/bin:$PATH"

# cd into install dir
cd "$SNAP_DATA" || exit 1
mkdir -p $SNAP_DATA/greengrass/v2 || exit 2
java -Droot=$SNAP_DATA/greengrass/v2 -Dlog.store=FILE -jar $SNAP/lib/Greengrass.jar \
     --start false --init-config $GREENGRASS_CONFIG --component-default-user root:root || exit 3


cd "$SNAP_DATA/greengrass/v2/alts/current/distro/bin" || exit 4
# TODO: Avoid running executables from write dir like $SNAP_DATA. Instead try running them from $SNAP
exec ./loader
