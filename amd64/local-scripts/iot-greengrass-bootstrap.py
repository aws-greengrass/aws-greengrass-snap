#!/usr/bin/env python3
import os
import sys
import json
import yaml
import zipfile
import subprocess
import time
import glob
from pathlib import Path

def load_bootstrap_config():
    """Load bootstrap configuration from pre-loaded config file"""
    config_paths = [
        f"{os.environ.get('SNAP_COMMON', '/tmp')}/bootstrap-config.yaml",
        "/var/snap/aws-iot-greengrass/common/bootstrap-config.yaml",
        "./bootstrap-config.yaml"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"[OK] Found bootstrap config: {config_path}")
            with open(config_path, 'r') as f:
                return yaml.safe_load(f), config_path
    
    print("[ERROR] No bootstrap-config.yaml found in expected locations:")
    for path in config_paths:
        print(f"  - {path}")
    return None, None

def get_device_name(config):
    """Get device name from config or prompt user"""
    device_name = config.get('deviceName')
    
    if not device_name or device_name == 'PROMPT':
        print("\n=== Device Configuration ===")
        device_name = input("Enter device name for IoT Core Thing: ").strip()
        if not device_name:
            print("[ERROR] Device name is required")
            return None
    
    print(f"[OK] Device name: {device_name}")
    return device_name

def validate_claim_certificates(config):
    """Validate that claim certificates exist and are readable"""
    cert_path = config.get('claimCertificatePath')
    key_path = config.get('claimPrivateKeyPath')
    
    if not cert_path or not key_path:
        print("[ERROR] Claim certificate paths not specified in config")
        return False
    
    if not os.path.exists(cert_path):
        print(f"[ERROR] Claim certificate not found: {cert_path}")
        return False
    
    if not os.path.exists(key_path):
        print(f"[ERROR] Claim private key not found: {key_path}")
        return False
    
    print(f"[OK] Claim certificate: {cert_path}")
    print(f"[OK] Claim private key: {key_path}")
    return True

def download_root_ca():
    """Download AWS IoT Root CA certificate"""
    import urllib.request
    
    certs_dir = f"{os.environ.get('SNAP_COMMON', '/tmp')}/certs"
    os.makedirs(certs_dir, exist_ok=True)
    root_ca_path = f"{certs_dir}/AmazonRootCA1.pem"
    
    if os.path.exists(root_ca_path):
        print(f"[OK] Root CA exists: {root_ca_path}")
        return root_ca_path
    
    try:
        url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        print(f"Downloading Root CA from {url}...")
        urllib.request.urlretrieve(url, root_ca_path)
        print(f"[OK] Downloaded Root CA: {root_ca_path}")
        return root_ca_path
    except Exception as e:
        print(f"[ERROR] Error downloading Root CA: {e}")
        return None

def create_fleet_provisioning_config(config, device_name, root_ca_path):
    """Create Greengrass config for fleet provisioning with claim certificates"""
    greengrass_root = f"{os.environ.get('SNAP_COMMON', '/tmp')}/greengrass/v2"
    os.makedirs(greengrass_root, exist_ok=True)
    
    region = config.get('awsRegion')
    template_name = config.get('provisioningTemplate')
    iot_data_endpoint = config.get('iotDataEndpoint')
    iot_cred_endpoint = config.get('iotCredEndpoint')
    
    # Build Greengrass config with fleet provisioning
    gg_config = {
        "system": {
            "certificateFilePath": config['claimCertificatePath'],
            "privateKeyPath": config['claimPrivateKeyPath'],
            "rootCaPath": root_ca_path,
            "rootpath": greengrass_root,
            "thingName": device_name
        },
        "services": {
            "aws.greengrass.Nucleus": {
                "componentType": "NUCLEUS",
                "version": config.get('nucleusVersion', '2.16.0'),
                "configuration": {
                    "awsRegion": region,
                    "iotRoleAlias": config.get('iotRoleAlias', 'GreengrassV2TokenExchangeRoleAlias'),
                    "iotDataEndpoint": iot_data_endpoint,
                    "iotCredEndpoint": iot_cred_endpoint,
                    "runWithDefault": {
                        "posixUser": "root"
                    }
                }
            },
            "aws.greengrass.FleetProvisioning": {
                "componentType": "PLUGIN",
                "configuration": {
                    "provisioningTemplate": template_name,
                    "claimCertificatePath": config['claimCertificatePath'],
                    "claimCertificatePrivateKeyPath": config['claimPrivateKeyPath'],
                    "rootCaPath": root_ca_path,
                    "awsRegion": region,
                    "iotDataEndpoint": iot_data_endpoint,
                    "templateParameters": {
                        "ThingName": device_name,
                        "SerialNumber": config.get('serialNumber', device_name)
                    }
                }
            }
        }
    }
    
    config_path = f"{greengrass_root}/config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(gg_config, f, default_flow_style=False)
    
    print(f"[OK] Created Greengrass config: {config_path}")
    return greengrass_root, config_path

def install_greengrass(greengrass_root, config_path):
    """Install Greengrass with fleet provisioning (daemon will start it)"""
    snap_dir = os.environ.get('SNAP', '/tmp')
    greengrass_zip = f"{snap_dir}/opt/greengrass/greengrass-nucleus.zip"
    
    if not os.path.exists(greengrass_zip):
        print(f"[ERROR] Greengrass installer not found: {greengrass_zip}")
        return False
    
    with zipfile.ZipFile(greengrass_zip, 'r') as zip_ref:
        zip_ref.extractall(greengrass_root)
    print("[OK] Extracted Greengrass installer")
    
    # Find Java
    java_paths = [
        f"{snap_dir}/usr/lib/jvm/java-11-openjdk-amd64/bin/java",
        f"{snap_dir}/usr/lib/jvm/java-11-openjdk-*/bin/java",
        "java"
    ]
    
    java_path = None
    for path in java_paths:
        if '*' in path:
            matches = glob.glob(path)
            if matches:
                java_path = matches[0]
                break
        elif os.path.exists(path):
            java_path = path
            break
    
    if not java_path:
        java_path = "java"
    
    print(f"[OK] Using Java: {java_path}")
    
    installer_jar = f"{greengrass_root}/lib/Greengrass.jar"
    fleetprovisioning_jar = f"{greengrass_root}/plugins/aws.greengrass.FleetProvisioningByClaim.jar"
    if not os.path.exists(installer_jar):
        print(f"[ERROR] Installer JAR not found: {installer_jar}")
        return False
    
    # Install Greengrass (setup only, don't start)
    install_cmd = [
        java_path,
        f"-Droot={greengrass_root}",
        "-Dlog.store=FILE",
        "-jar", installer_jar,
        "-trusted-plugin", fleetprovisioning_jar,
        "--init-config", config_path,
        "--component-default-user", "root:root",
        "--setup-system-service", "false",
        "--start", "false"
    ]
    
    print("Installing Greengrass...")
    result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode != 0:
        print(f"[ERROR] Installation failed: {result.stderr}")
        return False
    
    print("[OK] Greengrass installed")
    print("[INFO] Greengrass daemon will start automatically")
    print("[INFO] Fleet provisioning will begin when daemon starts")
    return True

def main():
    print("=" * 50)
    print("AWS IoT Greengrass Bootstrap Setup")
    print("(Fleet Provisioning with Claim Certificates)")
    print("=" * 50)
    
    # Load bootstrap config
    config, config_path = load_bootstrap_config()
    if not config:
        sys.exit(1)
    
    # Get device name
    device_name = get_device_name(config)
    if not device_name:
        sys.exit(1)
    
    # Validate claim certificates
    if not validate_claim_certificates(config):
        sys.exit(1)
    
    # Download Root CA
    root_ca_path = download_root_ca()
    if not root_ca_path:
        sys.exit(1)
    
    # Create Greengrass config
    greengrass_root, gg_config_path = create_fleet_provisioning_config(
        config, device_name, root_ca_path
    )
    
    # Install and start Greengrass
    if install_greengrass(greengrass_root, gg_config_path):
        print("\n" + "=" * 50)
        print("[OK] Bootstrap setup completed!")
        print("=" * 50)
        print(f"Device: {device_name}")
        print(f"Region: {config.get('awsRegion')}")
        print(f"Template: {config.get('provisioningTemplate')}")
        print("\nNext steps:")
        print("1. Start the Greengrass daemon:")
        print("   sudo snap start aws-iot-greengrass.greengrass-daemon")
        print("\n2. Monitor fleet provisioning:")
        print(f"   tail -f {greengrass_root}/logs/greengrass.log")
        print("\n3. Check daemon status:")
        print("   snap services aws-iot-greengrass")
        print("\nFleet provisioning will exchange claim certificates")
        print("for permanent device certificates automatically.")
    else:
        print("[ERROR] Bootstrap setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
