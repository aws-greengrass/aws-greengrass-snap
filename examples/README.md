# Overview 

This `examples` section contains boilerplate code for additional snaps that work with the main Greengrass snap.


## GG-Config Snap

This is a `content interface` **producer** snap that bundles the Greengrass config file along with device certs belonging to the device that is provisioned with Greengrass. 
The snap shares its content under `shared-files` with the **consumer** Greengrass snap. 

### Building the gg-config snap

This snap is a simple dump of all the content in `local-files` which is offers to share with consumer snaps under the `greengrass-config`  content interface. 
Once a consuming snap connects to `greengrass-config` plug, contents of `local-files` are available under `shared-files` in the target path of the consuming snap. 

Before building the snap, ensure to manually provision a Greengrass device as per instructions here. Copy over `config.yaml` to `shared-files`. Also copy over `device.pem.crt` , `private.pem.key`, `public.pem.key` and `AmazonRootCA1.pem` to a folder `gg-certs` under `shared-files` 
Refer to `shared-files` folder in examples to reference.

