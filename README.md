# AWS IoT Greengrass V2 as a Snap

## Overview

AWS IoT Greengrass snap 2.x enables you to run a limited version of AWS IoT Greengrass through convenient software packages, along with all necessary dependencies, in a containerized environment. You can use the Snapcraft.yaml file in this package to build a snap that runs on x86_64 platforms.

## Quickstart

### Building the Snap

We had trouble using the `snapcraft` command on our aws virtual
computers due to nested virtualization. If you run into problems,
we recommend that you copy our environments. We used Ubuntu 18.04+ on the
following ec2 instances:
* a metal x86 ec2
    * eg `m5.metal`

**These odd requirements are just for building the snap**. Once you have the
snap, you'll just need an OS that supports Snapcraft.
See https://snapcraft.io/docs/installing-snapd.

Dump this package onto your machine and `cd` into it.

Run `snapcraft`. This should generate the greengrass snap, you should see a snap appear in the package named something like
`aws-iot-greengrass-v2_2.4.0_amd64.snap`.

### Installing/Running the Snap

#### Installation

You can install the snap under
[`strict` confinement](https://snapcraft.io/docs/snap-confinement).
* For `strict` confinement, run
  `sudo snap install aws-iot-greengrass-v2_2.4.0_amd64.snap --dangerous`.

`aws-iot-greengrass-v2_*_*.snap` is supposed to be the file name of the snap you
created earlier.

You should now see it when you run `snap list`
```sh
ubuntu@ip-172-31-47-151:~/greengrass-snap/test$ snap list
Name                   Version           Rev    Tracking         Publisher   Notes
amazon-ssm-agent       3.0.1124.0        4046   latest/stable/…  aws✓        classic
aws-iot-greengrass-v2  2.4.0             x7     -                -           devmode
core18                 20210611          2074   latest/stable    canonical✓  base
core20                 20210702          1081   latest/stable    canonical✓  base
lxd                    4.0.7             21029  4.0/stable/…     canonical✓  -
multipass              1.7.0             5087   latest/stable    canonical✓  -
snapcraft              4.8.3             6596   latest/stable    canonical✓  classic
snapd                  2.51.3            12704  latest/stable    canonical✓  snapd
snappy-debug           0.36-snapd2.49.1  534    latest/stable    canonical✓  -
```

#### Greengrass manual provisioning

In order to run Greengrass you would need to follow the manual instruction guide here: https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html
First you must complete the following steps from the guide, to be able to provision your development device.
* [Create an AWS IoT thing](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#create-iot-thing)
* [Retrieve AWS IoT endpoints](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#retrieve-iot-endpoints)
* [Create a token exchange role](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#create-token-exchange-role)
* [Download certificates to the device](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#download-thing-certificates) 
  * Under `Download certificates to the device` section, make sure to replace `/greengrass/v2` with a folder in the user's `$HOME` dir. You will later connect the home interface to provide snap access to `$HOME` dir.


**Note:**   You will skip `Download the AWS IoT Greengrass Core software` step as this is handled by the Greengrass snap

Continue following the manual provisioning guide 
* [Install the AWS IoT Greengrass Core software](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#run-greengrass-core-v2-installer-manual)
  * Under this section, you only need to perform `step 2`. The goal is to create a config.yaml file with the device details from the above steps.
  * **Note:** Edit the `rootpath` in the config file to point to the root path inside the snap. In this case it would be `"/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"` 
  * Replace `certificateFilePath`, `privateKeyPath` and `rootCaPath` with their respective paths under `$HOME` dir. 
  * your config should look like so
    ```
    ---
    system:
        certificateFilePath: "/home/ubuntu/greengrass/v2/device.pem.crt"
        privateKeyPath: "/home/ubuntu/greengrass/v2/private.pem.key"
        rootCaPath: "/home/ubuntu/greengrass/v2/AmazonRootCA1.pem"
        rootpath: "/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"
        thingName: "MyGreengrassCoreSnap"
    services:
        aws.greengrass.Nucleus:
            componentType: "NUCLEUS"
            version: "2.4.0"
            configuration:
                awsRegion: "us-west-2"
                iotRoleAlias: "GreengrassCoreSnapTokenExchangeRoleAlias"
                iotDataEndpoint: "device-data-prefix-ats.iot.us-west-2.amazonaws.com"
                iotCredEndpoint: "device-credentials-prefix.credentials.iot.us-west-2.amazonaws.com"
    ```

Once you have this config.yaml created on your device, copy the file to the user's home directory.
You can then set the snap configuration with

```
sudo snap set aws-iot-greengrass-v2 greengrass-config=$HOME/config.yaml
```

#### Connect interfaces

As this snap is still in development, you must connect the interfaces explicitly before running the snap.
For the Greengrass snap to read the config file, connect the home interface with
```
sudo snap connect aws-iot-greengrass-v2:home-for-greengrass
```

Connect the other interfaces declared in `snapcraft.yaml` with

```
sudo snap connect aws-iot-greengrass-v2:hardware-observe
sudo snap connect aws-iot-greengrass-v2:log-observe
sudo snap connect aws-iot-greengrass-v2:mount-observe
sudo snap connect aws-iot-greengrass-v2:network-bind
sudo snap connect aws-iot-greengrass-v2:process-control
```

#### Start the snap

Choose how to start and run the Greengrass snap from the options listed below

* To start the greengrass service in the background, run with:
  ```
  sudo snap start aws-iot-greengrass-v2
  ```
  This command starts the service in the background, which is why it doesn't log any console output.
* You can choose to run the service with `--enable` option to enable the automatic starting of a service when the system boots
  ```
  sudo snap start --enable aws-iot-greengrass-v2.greengrass
  ```

Confirm that the greengrass service is active with `snap services aws-iot-greengrass-v2`
```
$ snap services aws-iot-greengrass-v2
Service                           Startup   Current   Notes
aws-iot-greengrass-v2.greengrass  disabled  active  -
```

#### Troubleshooting
If you run into trouble, first ensure that the greengrass service is stopped if currently running. Use `snap stop` to stop the service
```
sudo snap stop aws-iot-greengrass-v2.greengrass
```
Then run `sudo snap run` to start the service in the foreground.
```
sudo snap run aws-iot-greengrass-v2.greengrass
```
This command will run greengrass in the foreground allowing you to see console output which may be helpful when troubleshooting.

#### Removing the Snap

```sh
sudo snap remove --purge aws-iot-greengrass-v2
```
