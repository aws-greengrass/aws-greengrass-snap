# Bootstrap Setup - Implementation Guide

Complete guide for implementing fleet provisioning with claim certificates.

## Architecture

### Flow
```
Device Boot → Load Config → Validate Certs → Start Greengrass
    → Connect with Claim Cert → Fleet Provisioning
    → Exchange for Permanent Cert → Register as Core → Ready
```

### Certificate Lifecycle

**Claim Certificate** (pre-loaded):
- Limited permissions (provisioning only)
- Reusable across multiple devices
- Replaced after first boot

**Permanent Certificate** (auto-generated):
- Full Greengrass permissions
- Unique per device
- Used for all runtime operations

### File Structure
```
/var/snap/aws-iot-greengrass/common/
├── bootstrap-config.yaml              # Pre-loaded
├── claim-certs/
│   ├── claim.cert.pem                 # Pre-loaded
│   └── claim.private.key              # Pre-loaded
├── certs/
│   ├── AmazonRootCA1.pem             # Downloaded
│   ├── [device].cert.pem             # Generated
│   └── [device].private.key          # Generated
└── greengrass/v2/
    ├── config.yaml                    # Generated
    └── logs/greengrass.log
```

## AWS Account Setup

### 1. Create Provisioning Role

```bash
# Create role with trust policy
aws iam create-role \
  --role-name GreengrassProvisioningRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"iot.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# Attach AWS managed policy
aws iam attach-role-policy \
  --role-name GreengrassProvisioningRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTThingsRegistration

# Wait for role propagation
sleep 15
```

### 2. Create Device Policy

```bash
# Create policy (update REGION and ACCOUNT_ID)
aws iot create-policy \
  --policy-name GreengrassV2IoTThingPolicy \
  --policy-document file://device-policy.json
```

### 3. Create Provisioning Template

```bash
# Create template
aws iot create-provisioning-template \
  --template-name GreengrassFleetProvisioningTemplate \
  --provisioning-role-arn arn:aws:iam::ACCOUNT_ID:role/GreengrassProvisioningRole \
  --template-body file://provisioning-template.json \
  --enabled

# Verify
aws iot describe-provisioning-template \
  --template-name GreengrassFleetProvisioningTemplate
```

### 4. Generate Claim Certificates

```bash
chmod +x create-claim-certificates.sh
./create-claim-certificates.sh
```

Outputs to `claim-certificates/`:
- `claim.cert.pem` - Copy to devices
- `claim.private.key` - Copy to devices
- `bootstrap-config.yaml` - Copy to devices
- `claim-policy.json` - Reference only

## Device Preparation

### Build Snap Package

```bash
cd ~/mysnaps/aws-iot-greengrass
cp -r ~/git/aws-greengrass-snap/amd64/* .
./build.sh
```

### Pre-load Certificates (Manufacturing)

```bash
# Install snap
sudo snap install --dangerous ./aws-iot-greengrass_2.16.0_amd64.snap

# Create directories
sudo mkdir -p /var/snap/aws-iot-greengrass/common/claim-certs

# Copy certificates
sudo cp claim.cert.pem /var/snap/aws-iot-greengrass/common/claim-certs/
sudo cp claim.private.key /var/snap/aws-iot-greengrass/common/claim-certs/

# Set permissions
sudo chmod 644 /var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem
sudo chmod 600 /var/snap/aws-iot-greengrass/common/claim-certs/claim.private.key

# Copy config
sudo cp bootstrap-config.yaml /var/snap/aws-iot-greengrass/common/

# Connect interfaces
./connect.sh
```

### Configure Bootstrap Settings

Edit `/var/snap/aws-iot-greengrass/common/bootstrap-config.yaml`:

```yaml
awsRegion: "us-east-1"
deviceName: "PROMPT"  # or "GG-${SERIAL}" or fixed name
provisioningTemplate: "GreengrassFleetProvisioningTemplate"
iotDataEndpoint: "xxxxx.iot.us-east-1.amazonaws.com"
iotCredEndpoint: "xxxxx.credentials.iot.us-east-1.amazonaws.com"
iotRoleAlias: "GreengrassV2TokenExchangeRoleAlias"
claimCertificatePath: "/var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem"
claimPrivateKeyPath: "/var/snap/aws-iot-greengrass/common/claim-certs/claim.private.key"
```

Get endpoints:
```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS
aws iot describe-endpoint --endpoint-type iot:CredentialProvider
```

## Device Name Strategies

### Option 1: Manual Entry
```yaml
deviceName: "PROMPT"
```
User enters name during bootstrap.

### Option 2: Pre-configured
```yaml
deviceName: "Factory-Line-A-Device-001"
```
Fixed name set during manufacturing.

### Option 3: Auto-generate (Enhanced Script)
```yaml
deviceName: "GG-${SERIAL}"        # Hardware serial
deviceName: "GG-${MAC_ADDRESS}"   # MAC address
```

To use enhanced script, update `snap/snapcraft.yaml`:
```yaml
bootstrap:
  command: bin/python3 $SNAP/bin/iot-greengrass-bootstrap-enhanced.py
```

## Deployment

### Per-Device Bootstrap

```bash
sudo aws-iot-greengrass.bootstrap
```

Monitor:
```bash
sudo tail -f /var/snap/aws-iot-greengrass/common/greengrass/v2/logs/greengrass.log
```

### Verification

```bash
# Check Thing created
aws iot describe-thing --thing-name YOUR_DEVICE_NAME

# Check certificate attached
aws iot list-thing-principals --thing-name YOUR_DEVICE_NAME

# Check Greengrass Core
aws greengrassv2 list-core-devices --region us-east-1
```

## Troubleshooting

### Bootstrap Fails

**Check certificates:**
```bash
ls -la /var/snap/aws-iot-greengrass/common/claim-certs/
sudo cat /var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem
```

**Validate config:**
```bash
cat /var/snap/aws-iot-greengrass/common/bootstrap-config.yaml
```

**Test connectivity:**
```bash
curl https://YOUR_IOT_ENDPOINT:8443
```

### Provisioning Fails

**Check claim certificate active:**
```bash
aws iot describe-certificate --certificate-id CERT_ID
```

**Verify template enabled:**
```bash
aws iot describe-provisioning-template --template-name YOUR_TEMPLATE
```

**Check role permissions:**
```bash
aws iam get-role --role-name GreengrassProvisioningRole
aws iam list-attached-role-policies --role-name GreengrassProvisioningRole
```

### Greengrass Won't Start

**Check logs:**
```bash
sudo tail -100 /var/snap/aws-iot-greengrass/common/greengrass/v2/logs/greengrass.log
```

**Verify Java:**
```bash
$SNAP/usr/lib/jvm/java-11-openjdk-amd64/bin/java -version
```

**Check config:**
```bash
cat /var/snap/aws-iot-greengrass/common/greengrass/v2/config.yaml
```

## Security Considerations

1. **Claim Certificate Security**
   - Store securely during manufacturing
   - Limit to provisioning permissions only
   - Rotate periodically (quarterly/annually)
   - Can be reused but consider security implications

2. **Device Policy**
   - Follow least privilege principle
   - Restrict to necessary resources
   - Review and update regularly

3. **Network Security**
   - Use TLS for all connections
   - Configure firewall rules
   - Consider VPN for sensitive deployments

4. **Audit and Monitoring**
   - Enable CloudWatch logging
   - Monitor provisioning success rates
   - Alert on failed attempts
   - Track certificate usage

## Production Checklist

- [ ] Provisioning template created and tested
- [ ] Claim certificates generated and secured
- [ ] Device policy configured with least privilege
- [ ] Bootstrap config template prepared
- [ ] Snap package built and tested
- [ ] Device image with pre-loaded certs created
- [ ] Deployment procedures documented
- [ ] Team trained on bootstrap process
- [ ] Monitoring and alerting configured
- [ ] Rollback plan prepared

## Maintenance

### Regular Tasks
- Monitor provisioning success rate
- Review failed provisioning attempts
- Check certificate expiration dates
- Update Greengrass version as needed

### Periodic Tasks
- Rotate claim certificates (quarterly/annually)
- Review and update provisioning template
- Audit device registrations
- Update documentation
- Test disaster recovery procedures

## Support

For quick reference, see [BOOTSTRAP-QUICKSTART.md](BOOTSTRAP-QUICKSTART.md)
