# Overview 

This `examples` section contains boilerplate code for additional snaps that work with the main Greengrass snap.


## GG-Config Snap

This is a `content interface` **producer** snap that bundles the Greengrass config file along with device certs belonging to the device that is provisioned with Greengrass. 
The snap shares its content under `shared-files` with the **consumer** Greengrass snap. 

## Building the gg-config snap

This snap is a simple dump of all the content in `local-files` which is offers to share with consumer snaps under the `greengrass-config-content`  content interface. 
Once a consuming snap connects to `greengrass-config-content` plug, contents of `local-files` are available under `shared-files` in the target path of the consuming snap. 

Before building the snap, modify `config.yaml` to adjust all the filepaths.
* Ensure to manually provision a Greengrass device as per instructions under [pre-requisite here](../README.md#pre-requisite---manually-provision-a-greengrass-device). 
* Copy over `config.yaml` to `shared-files`. 
* Also copy over `device.pem.crt` , `private.pem.key`, `public.pem.key` and `AmazonRootCA1.pem` to a folder `gg-certs` under `shared-files`. Refer to `shared-files` folder in examples to reference.
* Edit the `rootpath` in the config file to point to the root path inside the snap. In this case it would be `"/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"`.
* Replace `certificateFilePath`, `privateKeyPath` and `rootCaPath` with their respective paths under the target path of the consuming Greengrass snap.
* your config should look like so
```
---
system:
  certificateFilePath: "/var/snap/aws-iot-greengrass-v2/current/greengrass/v2/shared-files/gg-certs/device.pem.crt"
  privateKeyPath: "/var/snap/aws-iot-greengrass-v2/current/greengrass/v2/shared-files/gg-certs/private.pem.key"
  rootCaPath: "/var/snap/aws-iot-greengrass-v2/current/greengrass/v2/shared-files/gg-certs/AmazonRootCA1.pem"
  rootpath: "/var/snap/aws-iot-greengrass-v2/current/greengrass/v2"
  thingName: "MyGGCoreCIS"
services:
  aws.greengrass.Nucleus:
    componentType: "NUCLEUS"
    version: "2.4.0"
    configuration:
      awsRegion: "us-west-2"
      iotRoleAlias: "GreengrassCoreTokenExchangeRoleAlias"
      iotDataEndpoint: "a6gwt5c3rk3kl-ats.iot.us-west-2.amazonaws.com"
      iotCredEndpoint: "cfm5sae6kdtaf.credentials.iot.us-west-2.amazonaws.com"

```

Now build the `gg-config` snap with 
```
snapcraft 
```
**Note**: you must be in the `gg-config` folder to run the above command.  
This should result in the `gg-config` snap with a name similar to `gg-config_0.1_amd64.snap`.

## Installing the gg-config snap

This snap should be installed in 
[`devmode` confinement](https://snapcraft.io/docs/snap-confinement).
* For `devmode` confinement, run
```sh
sudo snap install gg-config_0.1_amd64.snap --devmode
```

`gg-config_0.1_amd64.snap` is supposed to be the file name of the snap you
created earlier.

You should now see it when you run `snap list`
```sh
ubuntu@ip-172-31-47-151:~/greengrass-snap/test$ snap list
Name                   Version           Rev    Tracking         Publisher   Notes
amazon-ssm-agent       3.0.1124.0        4046   latest/stable/…  aws✓        classic
aws-iot-greengrass-v2  2.4.0             x7     -                -           -
gg-config              0.1         x1     -                -                 devmode
...
```
