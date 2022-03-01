#!/bin/bash -ex
#
# Copyright 2022 Canonical, Inc.
#
# This script is used to launch the jitp wait script in the background
# is it uses a blocking command (e.g. inotifywait) and there's no way to
# force a command into the background via snapcraft.yaml's command-line
# directive.
"$SNAP/wait-for-config.sh" &
