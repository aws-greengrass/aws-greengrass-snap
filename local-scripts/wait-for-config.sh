#!/bin/bash -ex
#
# Copyright 2022 Canonical, Inc.
#
# This script is used to wait for Greengrass credentials to be made available
# by a configuration snap using the greengrass-config content interface. This
# is necessary as devices using JITP (just-in-time-provisioning) do not have
# device credentials built in the OS image, but instead receive them on first
# boot via USB drive, or via remote RPC call to/from the device.
#
# This snap defines an content interface connect hook:
#
# connect_plug_greengrass_config_content
#
# ... which runs when the content interface between the greengrass snap and
# the config provider snap is connected. If the file 'config.yaml' is found,
# the connect hook sets the greengrass-config option, and starts the Nucleus.
# If 'config.yaml' is not found, then a oneshot service which runs this script
# is started.

config_dir="$SNAP_DATA/greengrass/v2/shared-files"
config_path="$config_dir/config.yaml"
no_config=true

while "$no_config"
do
  result=$(inotifywait -e moved_to -e close_write -q "$config_dir" | grep -o "config.yaml")
  echo "result=$result"

  if [ "$result" == "config.yaml" ]; then
     no_config=false
  fi
done

logger "aws-iot-greengrass::wait-for-config: setting greengrass-config=$config_path"
snapctl set greengrass-config="$config_path"
"$SNAP/snap/hooks/configure"

# zero exit code, so service doesn't get restarted
exit 0
