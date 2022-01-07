# AWS IoT Greengrass V2 as a Snap

## Overview

AWS IoT Greengrass snap 2.x enables you to run a limited version of AWS IoT Greengrass through convenient software packages, along with all necessary dependencies, in a containerized environment.
You can use the Snapcraft.yaml file in this package to build a snap that runs on x86_64 platforms.

## Pre-requisite - Manually provision a Greengrass device 

In order to run Greengrass you would need to follow the manual instruction guide here: https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html   
First you must complete the following steps from the guide, to be able to provision your development device.  
At the end of this process, you'll have a device manually provisioned with AWS IoT and a Greengrass config file that will later be used as a `snap configuration` in Greengrass snap. 

Follow these steps from AWS Greengrass docs:
* [Create an AWS IoT thing](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#create-iot-thing)
* [Retrieve AWS IoT endpoints](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#retrieve-iot-endpoints)
* [Create a token exchange role](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#create-token-exchange-role)
* [Download certificates to the device](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#download-thing-certificates)
  * Under `Download certificates to the device` section, make sure to replace `/greengrass/v2` with a folder you want to use.
  * **Remember this folder where the certs are stored.**
* **Note:**   You will skip `Set up the device environment` and `Download the AWS IoT Greengrass Core software` step as these are handled by the Greengrass snap
* [Install the AWS IoT Greengrass Core software](https://docs.aws.amazon.com/greengrass/v2/developerguide/manual-installation.html#run-greengrass-core-v2-installer-manual)
  * Under this section, you only need to perform `step 2`. The goal is to create a config.yaml file with the device details from the above steps.
  * **Note:** Edit the `rootpath` in the config file to point to the root path inside the snap. In this case it would be `"/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"`
  * Notice the `certificateFilePath`, `privateKeyPath` and `rootCaPath`. We will edit these in the next sections based on the method chosen to set `snap configuration` in Greengrass snap.
  * For the moment your config should look like so
    ```
    ---
    system:
        certificateFilePath: "/greengrass/v2/device.pem.crt"
        privateKeyPath: "/greengrass/v2/private.pem.key"
        rootCaPath: "/greengrass/v2/AmazonRootCA1.pem"
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

At the end of the process, you should have the config.yaml and a folder containing device certs. See [example folder here](examples/gg-config/local-files/shared-files)

## How is Greengrass config used in Greengrass snap 

Greengrass config file `config.yaml` from the above section gets used as an initial configuration in this Greengrass snap. 
See [reference](https://github.com/aws-greengrass/aws-greengrass-snap/blob/main/local-scripts/exec-loader.sh#L17-L18).
This initial configuration is the file path to Greengrass `config.yaml` file from previous section. 
And it can be set via `snap configuration` options (`greengrass-config`) offered by the Greengrass snap. 
There are many ways to provide the Greengrass `config.yaml` file to Greengrass snap. Two such options are captured below. 
Choose either option to set the `greengrass-config` snap configuration option.   

**Note**: On ubuntu core systems where everything needs to be a snap, you can only use the second option - building the `gg-config` snap to support Greengrass snap.


### 1. Set `greengrass-config` snap configuration option with file path under $HOME dir
If you have access to the user's $HOME dir, you can use this method to save `config.yaml` file under $HOME dir and specify the file path directly while setting `greengrass-config` snap configuration option.

* From the previous section, copy over `config.yaml` to the user's $HOME directory.
* Note `device.pem.crt` , `private.pem.key` and `AmazonRootCA1.pem` must also be saved under the $HOME dir.
* Edit the `rootpath` in the config file to point to the root path inside the snap. In this case it would be `"/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"` . You should've already made this change in the previous section.
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

Note the file path to `config.yaml`. In this case it should be `$HOME/config.yaml`. We will use this in later sections to set the snap configuration option.



### 2. Set `greengrass-config` snap configuration option using content interface

On ubuntu core systems where everything needs to be a snap, you can only use this option. 
With this approach, you will first build a producer snap (`gg-config`) that provides the greengrass `config.yaml`and device files via a `content interface` slot. 
You will then connect the `content interface` plug from Greengrass snap to this `gg-config` snap. Once the interface is connected, files from `gg-config` snap will be available in Greengrass snap under a `target path`.

Instructions to build the Content interface producer snap (`gg-config`) are under [the examples folder](examples/README.md).
At the end of the process, you should have a `gg-config` snap installed with the right set of `config.yaml` and device certs. 


## Building the Greengrass Snap

Now that Greengrass device is provisioned and `config.yaml` ready for consumption, let's build the Greengrass snap. 

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

## Installing the Greengrass Snap 

You can install the snap under
[`strict` confinement](https://snapcraft.io/docs/snap-confinement).
* For `strict` confinement, run
```sh
sudo snap install aws-iot-greengrass-v2_2.4.0_amd64.snap --dangerous
```

`aws-iot-greengrass-v2_*_*.snap` is supposed to be the file name of the snap you
created earlier.

You should now see it when you run `snap list`
```sh
ubuntu@ip-172-31-47-151:~/greengrass-snap/test$ snap list
Name                   Version           Rev    Tracking         Publisher   Notes
amazon-ssm-agent       3.0.1124.0        4046   latest/stable/…  aws✓        classic
aws-iot-greengrass-v2  2.4.0             x7     -                -           -
...
```

## Running the Greengrass Snap

### Connect interfaces

As this snap is still in development, you must connect the interfaces explicitly before running the snap.
Connect the interfaces declared in `snapcraft.yaml` with

```
sudo snap connect aws-iot-greengrass-v2:hardware-observe
sudo snap connect aws-iot-greengrass-v2:log-observe
sudo snap connect aws-iot-greengrass-v2:mount-observe
sudo snap connect aws-iot-greengrass-v2:network-bind
sudo snap connect aws-iot-greengrass-v2:process-control
sudo snap connect aws-iot-greengrass-v2:docker-executables docker:docker-executables
sudo snap connect aws-iot-greengrass-v2:docker-cli docker:docker-daemon
sudo snap connect aws-iot-greengrass-v2:root-dot-docker :personal-files
```

For the Greengrass snap to read the config file, connect the right interface that will allow access to greengrass `config.yaml` file.  
Choose one of the options bellow:

1. If in the [above greengrass config](#how-is-greengrass-config-used-in-greengrass-snap) section you chose [option 1](#1-set-greengrass-config-snap-configuration-option-with-file-path-under-home-dir), connect the home interface
    ```
    sudo snap connect aws-iot-greengrass-v2:home-for-greengrass
    ```
    
    Now that all the interfaces are connected, set the `greengrass-config` configuration option. In this case, it is the `config.yaml` filepath under $HOME dir.
    ```
    sudo snap set aws-iot-greengrass-v2 greengrass-config=$HOME/config.yaml
    ```

2. OR if you chose [option 2](#2-set-greengrass-config-snap-configuration-option-using-content-interface), connect the `greengrass-config-content` interface
    ```
    sudo snap connect aws-iot-greengrass-v2:greengrass-config-content gg-config:greengrass-config-content
    ```
    
    Now set the `greengrass-config` configuration option. In this case, it is the `config.yaml` filepath under the content interface's `target path` of Greengrass snap.
    ```
    sudo snap set aws-iot-greengrass-v2 greengrass-config=/var/snap/aws-iot-greengrass-v2/current/greengrass/v2/shared-files/config.yaml
    ```

### Start the snap

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

## Troubleshooting
If you run into trouble, first ensure that the greengrass service is stopped if currently running. Use `snap stop` to stop the service
```
sudo snap stop aws-iot-greengrass-v2.greengrass
```
Then run `sudo snap run` to start the service in the foreground.
```
sudo snap run aws-iot-greengrass-v2.greengrass
```
This command will run greengrass in the foreground allowing you to see console output which may be helpful when troubleshooting.

## Removing the Greengrass Snap

```sh
sudo snap remove --purge aws-iot-greengrass-v2
```
