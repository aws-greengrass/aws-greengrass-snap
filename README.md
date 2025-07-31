# Greengrass (Nucleus Classic) Ubuntu Core Snap Packages

These folders contain the Greengrass v2 Nucleus Classic Snap packages for Ubuntu Core

- arm64 package tested on Raspberry Pi Zero 2W running Ubuntu Core 22 fro Raspberry Pi Imager - To be updated
- amd64 tested on Intel NUC N150 running generic Ubuntu Core 24 image from Canonical

## Building the snap

1. Install Snapcraft

    sudo snap install snapcraft

2. Create a new folder in your home folder (e.g. /home/user/mysnaps/aws-iot-greengrass)

3. Change to the folder you just created and initialize snapcraft

    cd ~/mysnaps/aws-iot-greengrass
    snapcraft init

4. Copy all files from this repository to local machine.  The snapcraft init command from the previous step creates a default snapcraft.yaml file - replace that default file with the one in this repository

5. Run the following script to build the new snap;

    ./build.sh

## Installation

Copy *.snap package locally to the device (use SCP) and execute installation

    sudo snap install --dangerous ./aws-iot-greengrass_1.0_<arch>.snap

Once installed successfully, configure Greengrass using the following commands:

    ./connect.sh
    sudo aws-iot-greengrass-setup.configure

The `connect.sh` script connects the installed Greengrass package to the Ubuntu Core slots that are not connected by default. (should not be needed once published to Snap store)

The `sudo aws-iot-greengrass.configure` command prompts for the following information;
- AWS Access Key
- AWS Secret Access Key
- AWS Region
- Device Name (for IoT Core Thing and Greengrass Core Device name)

The Access Key/Secret Access Key corresponds to an IAM user with sufficient privileges to install and connect an IoT Thing to IoT Core, including provisioning certificates, and creating the Greengrass Core device.  

**NOTE**: This command also assumes that the role alias `GreengrassV2TokenExchangeRoleAlias` already exists and this should refer to a suitable IAM role.



