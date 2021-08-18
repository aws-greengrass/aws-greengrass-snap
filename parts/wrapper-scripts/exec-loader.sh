#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# This script is necessary because loader script needs to be executed from
# $SNAP_DATA/greengrass/v2/alts/current/distro/bin path.
# Referencing this path from the snapcraft.yaml file results in path does not exist errors

set -o xtrace

cd "$SNAP_DATA/greengrass/v2/alts/current/distro/bin" || exit 1
# TODO: Avoid running executables from write dir like $SNAP_DATA. Instead try running them from $SNAP
exec ./loader