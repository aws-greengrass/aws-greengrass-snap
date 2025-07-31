import os
import sys
import json
import zipfile
import subprocess
import time
import glob
import boto3
from botocore.exceptions import ClientError
import yaml

def get_aws_credentials():
    """Get AWS credentials from user input"""
    print("=== AWS Configuration ===")
    access_key = input("Enter AWS Access Key ID: ").strip()
    secret_key = input("Enter AWS Secret Access Key: ").strip()
    region = input("Enter AWS Region (e.g., us-east-1): ").strip()

    if not all([access_key, secret_key, region]):
        print("Error: All AWS credentials are required")
        return None, None, None

    return access_key, secret_key, region

def get_device_info():
    """Get device information from user"""
    print("\n=== Device Configuration ===")
    device_name = input("Enter device name: ").strip()

    if not device_name:
        print("Error: Device name is required")
        return None

    return device_name

def create_aws_clients(access_key, secret_key, region):
    """Create AWS service clients"""
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        iot_client = session.client('iot')
        iam_client = session.client('iam')
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']

        return iot_client, iam_client, account_id
    except Exception as e:
        print(f"Error creating AWS clients: {e}")
        return None, None

def get_iot_endpoints(iot_client):
    """Get IoT endpoints from AWS API"""
    print("\n=== Getting IoT Endpoints ===")
    try:
        # Get data endpoint (ATS)
        data_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
        iot_data_endpoint = data_response['endpointAddress']
        print(f"✓ Data endpoint: {iot_data_endpoint}")

        # Get credentials endpoint
        cred_response = iot_client.describe_endpoint(endpointType='iot:CredentialProvider')
        iot_cred_endpoint = cred_response['endpointAddress']
        print(f"✓ Credentials endpoint: {iot_cred_endpoint}")

        # Use data endpoint as core endpoint (they're the same for ATS)
        iot_core_endpoint = iot_data_endpoint
        print(f"✓ Core endpoint: {iot_core_endpoint}")

        return iot_core_endpoint, iot_data_endpoint, iot_cred_endpoint

    except Exception as e:
        print(f"Error getting IoT endpoints: {e}")
        return None, None, None

def create_iot_thing_type(iot_client, thing_type_name):
    """Create IoT thing type for Greengrass"""
    try:
        response = iot_client.create_thing_type(
            thingTypeName=thing_type_name,
            thingTypeProperties={
                'thingTypeDescription': 'Greengrass Core Device'
            }
        )
        print(f"✓ Successfully created IoT thing type: {thing_type_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print(f"⚠ IoT thing type '{thing_type_name}' already exists")
        else:
            raise e

def create_iot_thing(iot_client, thing_name, thing_type_name):
    """Create IoT thing"""
    try:
        response = iot_client.create_thing(
            thingName=thing_name,
            thingTypeName=thing_type_name
        )
        print(f"✓ Successfully created IoT thing: {thing_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print(f"⚠ IoT thing '{thing_name}' already exists")
        else:
            raise e

def create_device_certificate(iot_client, thing_name):
    """Create and activate device certificate"""
    try:
        # Create certificate
        response = iot_client.create_keys_and_certificate(setAsActive=True)

        cert_arn = response['certificateArn']
        cert_id = response['certificateId']
        cert_pem = response['certificatePem']
        private_key = response['keyPair']['PrivateKey']

        print(f"✓ Created certificate: {cert_id}")
        print(f"✓ Certificate ARN: {cert_arn}")

        # Save certificate and key files
        certs_dir = f"{os.environ.get('SNAP_COMMON', '/tmp')}/certs"
        os.makedirs(certs_dir, exist_ok=True)

        cert_path = f"{certs_dir}/{thing_name}.cert.pem"
        key_path = f"{certs_dir}/{thing_name}.private.key"

        with open(cert_path, 'w') as f:
            f.write(cert_pem)

        with open(key_path, 'w') as f:
            f.write(private_key)

        # Set appropriate permissions
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)

        print(f"✓ Saved certificate to: {cert_path}")
        print(f"✓ Saved private key to: {key_path}")

        # Attach certificate to thing
        iot_client.attach_thing_principal(
            thingName=thing_name,
            principal=cert_arn
        )
        print(f"✓ Attached certificate to thing: {thing_name}")

        return cert_arn, cert_id, cert_path, key_path

    except Exception as e:
        print(f"Error creating device certificate: {e}")
        return None, None, None, None

def create_greengrass_policy(iot_client, policy_name, region, account_id):
    """Create IoT policy for Greengrass device"""
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iot:Connect",
                    "iot:Publish",
                    "iot:Subscribe",
                    "iot:Receive"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "greengrass:*"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iot:AssumeRoleWithCertificate"
                ],
                "Resource": [
                    f"arn:aws:iot:{region}:{account_id}:rolealias/GreengrassV2TokenExchangeRoleAlias"
                ]
            }
        ]
    }

    try:
        response = iot_client.create_policy(
            policyName=policy_name,
            policyDocument=json.dumps(policy_document)
        )
        print(f"✓ Created IoT policy: {policy_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print(f"⚠ IoT policy '{policy_name}' already exists")
        else:
            raise e

def attach_policy_to_certificate(iot_client, policy_name, cert_arn):
    """Attach policy to certificate"""
    try:
        iot_client.attach_principal_policy(
            policyName=policy_name,
            principal=cert_arn
        )
        print(f"✓ Attached policy '{policy_name}' to certificate")
    except Exception as e:
        print(f"Error attaching policy to certificate: {e}")

def download_root_ca():
    """Download AWS IoT Root CA certificate"""
    import requests

    certs_dir = f"{os.environ.get('SNAP_COMMON', '/tmp')}/certs"
    root_ca_path = f"{certs_dir}/AmazonRootCA1.pem"

    if os.path.exists(root_ca_path):
        print(f"✓ Root CA already exists: {root_ca_path}")
        return root_ca_path

    try:
        url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(root_ca_path, 'w') as f:
            f.write(response.text)

        print(f"✓ Downloaded Root CA to: {root_ca_path}")
        return root_ca_path

    except Exception as e:
        print(f"Error downloading Root CA: {e}")
        return None

def install_greengrass_v2(thing_name, region, cert_path, private_key_path, root_ca_path, 
                         iot_core_endpoint, iot_data_endpoint, iot_cred_endpoint):
    """Install and configure AWS Greengrass v2"""
    print("\n=== Installing AWS Greengrass v2 ===")

    # Create Greengrass directory
    greengrass_root = f"{os.environ.get('SNAP_COMMON', '/tmp')}/greengrass/v2"
    os.makedirs(greengrass_root, exist_ok=True)

    # Extract Greengrass installer
    snap_dir = os.environ.get('SNAP', '/tmp')
    greengrass_zip = f"{snap_dir}/opt/greengrass/greengrass-nucleus.zip"

    if os.path.exists(greengrass_zip):
        with zipfile.ZipFile(greengrass_zip, 'r') as zip_ref:
            zip_ref.extractall(greengrass_root)
        print("✓ Extracted Greengrass v2 installer")
    else:
        print("⚠ Greengrass installer not found in snap")
        return False

    iot_role_alias = "GreengrassV2TokenExchangeRoleAlias"

    # Create Greengrass configuration with all IoT endpoints
    config = {
        "system": {
            "certificateFilePath": cert_path,
            "privateKeyPath": private_key_path,
            "rootCaPath": root_ca_path,
            "rootpath": greengrass_root,
            "thingName": thing_name
        },
        "services": {
            "aws.greengrass.Nucleus": {
                "componentType": "NUCLEUS",
                "version": "2.12.0",
                "configuration": {
                    "awsRegion": region,
                    "iotRoleAlias": iot_role_alias,
                    "iotDataEndpoint": iot_data_endpoint,
                    "iotCredEndpoint": iot_cred_endpoint,
                    "runWithDefault": {
                        "posixUser": "root"
                    }
                }
            }
        }
    }

    config_path = f"{greengrass_root}/config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✓ Created Greengrass configuration at {config_path}")
    print(f"  IoT Core Endpoint: {iot_core_endpoint}")
    print(f"  IoT Data Endpoint: {iot_data_endpoint}")
    print(f"  IoT Cred Endpoint: {iot_cred_endpoint}")

    # Find and test Java binary
    snap_dir = os.environ.get('SNAP', '')
    possible_java_paths = [
        f"{snap_dir}/usr/lib/jvm/java-11-openjdk-amd64/bin/java",
        f"{snap_dir}/usr/lib/jvm/java-11-openjdk-*/bin/java",
        f"{snap_dir}/usr/bin/java",
        "/usr/bin/java",
        "java"
    ]

    java_path = None
    for path in possible_java_paths:
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

    print(f"Using Java at: {java_path}")

    # Test Java installation
    try:
        java_test = subprocess.run([java_path, "-version"], 
                                 capture_output=True, text=True, timeout=10)
        java_version = java_test.stderr.split('\n')[0] if java_test.stderr else "Unknown"
        print(f"✓ Java version: {java_version}")
    except Exception as e:
        print(f"⚠ Java test failed: {e}")
        return False

    # Check installer JAR
    installer_jar = f"{greengrass_root}/lib/Greengrass.jar"
    if not os.path.exists(installer_jar):
        print(f"⚠ Greengrass installer JAR not found at: {installer_jar}")
        print("Contents of Greengrass root:")
        for root, dirs, files in os.walk(greengrass_root):
            level = root.replace(greengrass_root, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        return False

    print(f"✓ Found installer JAR at: {installer_jar}")

    # Install Greengrass with debugging
    try:
        install_cmd = [
            java_path,
            "-Droot=" + greengrass_root,
            "-Dlog.store=FILE",
            "-jar", installer_jar,
            "--init-config", config_path,
            "--component-default-user", "root:root",
            "--setup-system-service", "false",
            "--start", "false"
        ]

        print(f"Installing Greengrass (without auto-start)...")
        print(f"Command: {' '.join(install_cmd)}")

        result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=120)

        print(f"Installation completed with return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        # Check if installation created necessary files
        nucleus_jar = f"{greengrass_root}/alts/current/distro/lib/Greengrass.jar"
        if os.path.exists(nucleus_jar):
            print("✓ Greengrass installation completed successfully")

            # Start Greengrass with debugging
            print("\n=== Starting Greengrass Nucleus ===")
            start_result = start_greengrass_with_debugging(greengrass_root, java_path)

            if start_result:
                print("✓ Greengrass v2 is running")
                print(f"✓ Monitor logs: tail -f {greengrass_root}/logs/greengrass.log")
                print(f"✓ Greengrass root: {greengrass_root}")
            else:
                print("⚠ Greengrass installed but startup had issues")
                print("Manual start command:")
                print(f"  cd {greengrass_root}")
                print(f"  {java_path} -Droot={greengrass_root} -jar alts/current/distro/lib/Greengrass.jar")

            return True
        else:
            print("⚠ Installation completed but Nucleus JAR not found")
            return False

    except subprocess.TimeoutExpired:
        print("⚠ Installation timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"Error during Greengrass installation: {e}")
        return False

def start_greengrass_with_debugging(greengrass_root, java_path):
    """Start Greengrass with debugging output"""
    try:
        nucleus_jar = f"{greengrass_root}/alts/current/distro/lib/Greengrass.jar"

        start_cmd = [
            java_path,
            "-Droot=" + greengrass_root,
            "-Dlog.store=FILE",
            "-jar", nucleus_jar
        ]

        print(f"Starting Greengrass: {' '.join(start_cmd)}")
        print("Starting in background (monitoring for 15 seconds)...")

        # Start as background process
        process = subprocess.Popen(start_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Monitor startup for 15 seconds
        for i in range(15):
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"Process exited early with code: {process.returncode}")
                if stdout:
                    print(f"STDOUT: {stdout}")
                if stderr:
                    print(f"STDERR: {stderr}")
                return False

            print(f"  Startup check {i+1}/15 - Process running (PID: {process.pid})")

        print("✓ Greengrass appears to be running successfully")
        print(f"✓ Process ID: {process.pid}")

        # Check if log file exists and show recent entries
        log_file = f"{greengrass_root}/logs/greengrass.log"
        if os.path.exists(log_file):
            print(f"✓ Log file created: {log_file}")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print("Recent log entries:")
                        for line in lines[-5:]:  # Show last 5 lines
                            print(f"  {line.strip()}")
            except:
                pass

        return True

    except Exception as e:
        print(f"Error starting Greengrass: {e}")
        return False

def main():
    """Main setup function"""

    print(f"AWS IoT Core and Greengrass Setup")
    print("=" * 40)

    # Get AWS credentials
    access_key, secret_key, region = get_aws_credentials()
    if not all([access_key, secret_key, region]):
        sys.exit(1)

    # Get device information
    device_name = get_device_info()
    if not device_name:
        sys.exit(1)

    # Create AWS clients
    iot_client, iam_client, account_id = create_aws_clients(access_key, secret_key, region)
    if not iot_client:
        sys.exit(1)

    print(f"\n=== Configuring Greengrass Core: {device_name} ===")

    try:
        # Get IoT endpoints
        iot_core_endpoint, iot_data_endpoint, iot_cred_endpoint = get_iot_endpoints(iot_client)
        if not all([iot_core_endpoint, iot_data_endpoint, iot_cred_endpoint]):
            print("Failed to get IoT endpoints")
            sys.exit(1)

        # Create IoT thing type
        thing_type_name = "GreengrassCore"
        create_iot_thing_type(iot_client, thing_type_name)

        # Create IoT thing
        create_iot_thing(iot_client, device_name, thing_type_name)

        # Create device certificate
        cert_arn, cert_id, cert_path, key_path = create_device_certificate(iot_client, device_name)
        if not cert_arn:
            print("Failed to create device certificate")
            sys.exit(1)

        # Create and attach policy
        policy_name = f"{device_name}-GreengrassV2IoTThingPolicy"
        create_greengrass_policy(iot_client, policy_name, region, account_id)
        attach_policy_to_certificate(iot_client, policy_name, cert_arn)

        # Download Root CA
        root_ca_path = download_root_ca()
        if not root_ca_path:
            print("Failed to download Root CA")
            sys.exit(1)

        # Install Greengrass v2
        success = install_greengrass_v2(device_name, region, cert_path, key_path, root_ca_path,
                                      iot_core_endpoint, iot_data_endpoint, iot_cred_endpoint)

        if success:
            print("\n" + "=" * 50)
            print("✓ AWS IoT Greengrass v2 setup completed successfully!")
            print("=" * 50)
            print(f"Device Name: {device_name}")
            print(f"Certificate ARN: {cert_arn}")
            print(f"IoT Core Endpoint: {iot_core_endpoint}")
            print(f"Policy: {policy_name}")
            print(f"Region: {region}")
        else:
            print("\n⚠ Setup completed with issues. Check the logs above.")
            sys.exit(1)

    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
