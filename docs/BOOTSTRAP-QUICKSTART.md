# Bootstrap Setup - Quick Start

Fleet provisioning with pre-loaded claim certificates for manufacturing and production deployments.

## Overview

Bootstrap setup uses claim certificates pre-loaded on devices to automatically provision Greengrass via AWS IoT Fleet Provisioning. Ideal for manufacturing scenarios.

## Prerequisites

- AWS account with IoT Core access
- Provisioning template created in AWS
- Claim certificates generated
- `GreengrassV2TokenExchangeRoleAlias` exists

## Quick Setup

### 1. AWS Setup (One-time)

```bash
# Generate claim certificates
cd amd64
chmod +x create-claim-certificates.sh
./create-claim-certificates.sh
```

This creates `claim-certificates/` with:
- Claim certificate and key
- Bootstrap configuration
- IoT policy

### 2. Device Setup

```bash
# Install snap
sudo snap install --dangerous ./aws-iot-greengrass_2.16.0_amd64.snap
./connect.sh

# Copy claim certificates
sudo mkdir -p /var/snap/aws-iot-greengrass/common/claim-certs
sudo cp claim.cert.pem /var/snap/aws-iot-greengrass/common/claim-certs/
sudo cp claim.private.key /var/snap/aws-iot-greengrass/common/claim-certs/
sudo chmod 644 /var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem
sudo chmod 600 /var/snap/aws-iot-greengrass/common/claim-certs/claim.private.key

# Copy bootstrap config
sudo cp bootstrap-config.yaml /var/snap/aws-iot-greengrass/common/

# Run bootstrap
sudo aws-iot-greengrass.bootstrap
```

### 3. Verify

```bash
# Monitor logs
sudo tail -f /var/snap/aws-iot-greengrass/common/greengrass/v2/logs/greengrass.log

# Check in AWS Console
aws iot list-things --region us-east-1
```

## Device Name Options

**Prompt during setup:**
```yaml
deviceName: "PROMPT"
```

**Pre-configured:**
```yaml
deviceName: "Factory-Device-001"
```

**Auto-generate (enhanced script):**
```yaml
deviceName: "GG-${SERIAL}"  # or ${MAC_ADDRESS}
```

## Comparison

| Feature | Interactive Setup | Bootstrap Setup |
|---------|------------------|-----------------|
| User input | AWS credentials + device name | Device name only |
| Pre-config | None | Claim certs + config |
| Scalability | Low | High |
| Best for | Development | Production/Fleet |

## Troubleshooting

**Certificates not found:**
```bash
ls -la /var/snap/aws-iot-greengrass/common/claim-certs/
```

**Config missing:**
```bash
cat /var/snap/aws-iot-greengrass/common/bootstrap-config.yaml
```

**Check connectivity:**
```bash
curl https://YOUR_IOT_ENDPOINT:8443
```

For detailed setup, see [BOOTSTRAP-GUIDE.md](BOOTSTRAP-GUIDE.md)
