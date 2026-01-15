# Greengrass (Nucleus Classic) Ubuntu Core Snap Packages

These folders contain the Greengrass v2 Nucleus Classic Snap packages for Ubuntu Core

- arm64 package tested on Raspberry Pi Zero 2W running Ubuntu Core 22 from Raspberry Pi Imager
- amd64 tested on Intel NUC N150 running generic Ubuntu Core 24 image from Canonical

## Building the snap

Install Snapcraft

```bash
sudo snap install snapcraft
```

Install necessary tools

```bash
sudo apt install findutils python3-dev python3-venv wget
```
Create a new folder in your home folder (e.g. `/home/user/mysnaps/aws-iot-greengrass`)

Change to the folder you just created and initialize snapcraft

```bash
mkdir -p ~/mysnaps/aws-iot-greengrass
cd ~/mysnaps/aws-iot-greengrass
snapcraft init
```

Copy all files from the amd64 or arm64 repository to local machine.  The `snapcraft init` command from the previous step creates a default `snapcraft.yaml` file - replace that default file with the one in this repository

```bash
cp -r  ~/git/aws-greengrass-snap/amd64/* ~/mysnaps/aws-iot-greengrass
```

Run the following script to build the new snap

```bash
./build.sh
```

## Installation

Copy *.snap package locally to the device (use SCP) and execute installation

```bash
sudo snap install --dangerous ./aws-iot-greengrass_<version>_<arch>.snap
```

## Configuration

There are two ways to configure Greengrass after installation:

### Option 1: Interactive Setup (Development/Testing)

Best for individual devices and development environments.

```bash
./connect.sh
sudo aws-iot-greengrass.configure
```

The `sudo aws-iot-greengrass.configure` command prompts for:
- AWS Access Key
- AWS Secret Access Key
- AWS Region
- Device Name (for IoT Core Thing and Greengrass Core Device name)

The Access Key/Secret Access Key corresponds to an IAM user with sufficient privileges to install and connect an IoT Thing to IoT Core, including provisioning certificates, and creating the Greengrass Core device.

### Option 2: Bootstrap Setup with Claim Certificates (Fleet Provisioning)

Best for manufacturing and fleet deployments where devices are pre-configured.

```bash
./connect.sh
sudo aws-iot-greengrass.bootstrap
```

This approach uses pre-loaded claim certificates for fleet provisioning. See:
- **[docs/BOOTSTRAP-QUICKSTART.md](docs/BOOTSTRAP-QUICKSTART.md)** - Quick start guide
- **[docs/BOOTSTRAP-GUIDE.md](docs/BOOTSTRAP-GUIDE.md)** - Detailed implementation guide
- **[docs/BOOTSTRAP-OVERVIEW.md](docs/BOOTSTRAP-OVERVIEW.md)** - Solution overview and architecture

The `connect.sh` script connects the installed Greengrass package to the Ubuntu Core slots that are not connected by default. (should not be needed once published to Snap store)

## NOTES

- The package assumes that the role alias `GreengrassV2TokenExchangeRoleAlias` already exists and this should refer to a suitable IAM role.
- Docker integration is included so the Docker snap must be installed (`snap install docker`) on the build machine to build successfully.
- Some Python libraries are included in the snap such as boto3 and awsiotsdk.  Further validation should be done on what should/should not be included
