# Bootstrap Setup - Solution Overview

## What is Bootstrap Setup?

Bootstrap setup enables automated Greengrass provisioning using pre-loaded claim certificates. Devices authenticate with temporary claim certificates and automatically receive permanent certificates via AWS IoT Fleet Provisioning.

## Use Cases

- **Manufacturing**: Pre-configure devices before shipping
- **Fleet Deployment**: Deploy hundreds/thousands of devices
- **Zero-Touch Provisioning**: Minimal user interaction required
- **Secure Deployment**: No AWS credentials on devices

## Solution Components

### Scripts
- **iot-greengrass-bootstrap.py** - Basic bootstrap with manual/pre-configured device names
- **iot-greengrass-bootstrap-enhanced.py** - Auto-detects hardware serial/MAC for device names
- **create-claim-certificates.sh** - Generates claim certificates and AWS resources

### Configuration
- **bootstrap-config.yaml** - Device configuration (region, endpoints, template)
- **provisioning-template.json** - AWS IoT provisioning template
- **device-policy.json** - IoT policy for provisioned devices
- **trust-policy.json** - IAM trust policy for provisioning role

## Architecture

### High-Level Flow
```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Device    │         │  Greengrass  │         │  AWS IoT    │
│    Boot     │────────>│   Bootstrap  │────────>│    Core     │
└─────────────┘         └──────────────┘         └─────────────┘
                              │                          │
                              │ Claim Cert               │
                              │─────────────────────────>│
                              │                          │
                              │ Permanent Cert           │
                              │<─────────────────────────│
                              │                          │
                              │ Register Core            │
                              │─────────────────────────>│
```

### Certificate Lifecycle
```
Manufacturing Phase:
  AWS Admin creates claim certificate
       ↓
  Pre-load on device
       ↓
  
Deployment Phase:
  Device boots with claim cert
       ↓
  Greengrass connects to IoT Core
       ↓
  Fleet provisioning exchanges certificates
       ↓
  Permanent cert stored, claim cert no longer used
       ↓
  Device registered as Greengrass Core
```

### File Locations
```
/var/snap/aws-iot-greengrass/common/
├── bootstrap-config.yaml              # Configuration
├── claim-certs/                       # Pre-loaded
│   ├── claim.cert.pem
│   └── claim.private.key
├── certs/                             # Runtime
│   ├── AmazonRootCA1.pem
│   ├── [device].cert.pem             # Generated
│   └── [device].private.key          # Generated
└── greengrass/v2/
    ├── config.yaml                    # Generated
    └── logs/greengrass.log
```

## How It Works

### 1. Pre-Configuration (Manufacturing)
- Generate claim certificates in AWS
- Create bootstrap configuration
- Pre-load certificates and config on device
- Install snap package

### 2. Device Boot (Deployment)
- Bootstrap script loads configuration
- Validates claim certificates exist
- Determines device name (prompt/auto/pre-configured)
- Configures Greengrass with claim certificates
- Starts Greengrass

### 3. Fleet Provisioning (Automatic)
- Greengrass connects to IoT Core with claim cert
- Fleet Provisioning plugin calls provisioning template
- AWS creates Thing, generates permanent certificate, attaches policy
- Permanent certificate returned to device
- Greengrass replaces claim cert with permanent cert
- Device registered as Greengrass Core

### 4. Runtime
- Device operates with permanent certificate
- Receives component deployments
- Communicates with AWS IoT Core
- Token exchange for AWS credentials

## Comparison: Interactive vs Bootstrap

| Aspect | Interactive Setup | Bootstrap Setup |
|--------|------------------|-----------------|
| **User Input** | AWS Access Key, Secret Key, Region, Device Name | Device Name only (optional) |
| **Pre-configuration** | None required | Claim certs + config required |
| **AWS Credentials** | Temporary on device | Never on device |
| **Certificate Creation** | Manual via API | Automatic via provisioning |
| **Setup Time** | 3-5 minutes | < 1 minute |
| **Scalability** | Low (one-by-one) | High (fleet) |
| **User Skill Required** | AWS knowledge | Minimal |
| **Best For** | Development, testing, individual devices | Manufacturing, production, fleet deployment |
| **Security** | Credentials temporarily on device | No credentials on device |

## Device Name Strategies

### Strategy 1: Prompt User
```yaml
deviceName: "PROMPT"
```
- User enters name during bootstrap
- Good for: Small deployments, unique naming requirements
- Requires: User interaction

### Strategy 2: Pre-configured
```yaml
deviceName: "Factory-A-Device-001"
```
- Fixed name in config file
- Good for: Known device assignments
- Requires: Unique config per device

### Strategy 3: Hardware Serial (Enhanced Script)
```yaml
deviceName: "GG-${SERIAL}"
```
- Auto-detects CPU serial number
- Good for: Raspberry Pi, devices with readable serial
- Requires: Enhanced bootstrap script

### Strategy 4: MAC Address (Enhanced Script)
```yaml
deviceName: "GG-${MAC_ADDRESS}"
```
- Auto-detects primary MAC address
- Good for: Any device with network interface
- Requires: Enhanced bootstrap script

## Security Model

### Claim Certificate
**Permissions:**
- Connect to IoT Core
- Publish/Subscribe to provisioning topics only
- Cannot access regular IoT operations

**Lifecycle:**
- Created once by AWS admin
- Reusable across multiple devices
- Replaced after first successful provisioning
- Should be rotated periodically

### Permanent Certificate
**Permissions:**
- Full IoT Core operations
- Greengrass operations
- Token exchange for AWS credentials
- Access to device-specific resources

**Lifecycle:**
- Created automatically during provisioning
- Unique per device
- Attached to specific Thing
- Used for all runtime operations

## Implementation Steps

### Phase 1: AWS Setup (One-time)
1. Create provisioning IAM role
2. Create device IoT policy
3. Create provisioning template
4. Generate claim certificates
5. Distribute certificates to manufacturing

### Phase 2: Manufacturing
1. Build snap package with bootstrap support
2. Install snap on device
3. Pre-load claim certificates
4. Pre-load bootstrap configuration
5. Create device image/snapshot

### Phase 3: Deployment
1. Device boots with pre-loaded config
2. Run bootstrap command
3. Enter device name (if required)
4. Wait for provisioning to complete
5. Verify in AWS Console

### Phase 4: Operations
1. Monitor provisioning success rate
2. Deploy Greengrass components
3. Manage device fleet
4. Rotate claim certificates periodically

## Benefits

✅ **Minimal User Interaction** - Only device name required, can be automated  
✅ **No AWS Credentials on Device** - Uses claim certificates instead  
✅ **Highly Scalable** - Single claim cert provisions entire fleet  
✅ **Manufacturing Friendly** - Pre-load during manufacturing  
✅ **Automatic Certificate Management** - Fleet provisioning handles rotation  
✅ **Secure** - Limited claim cert permissions, automatic upgrade to permanent  
✅ **Flexible Device Naming** - Multiple strategies supported  
✅ **Production Ready** - Tested and documented  

## Limitations

- Requires AWS IoT Fleet Provisioning setup
- Claim certificates must be pre-loaded
- Requires network connectivity on first boot
- Device name must be unique per AWS account/region

## Getting Started

1. **Quick Start**: See [BOOTSTRAP-QUICKSTART.md](BOOTSTRAP-QUICKSTART.md)
2. **Detailed Guide**: See [BOOTSTRAP-GUIDE.md](BOOTSTRAP-GUIDE.md)
3. **Main README**: See [../README.md](../README.md)

## Support and Troubleshooting

Common issues and solutions in [BOOTSTRAP-GUIDE.md](BOOTSTRAP-GUIDE.md#troubleshooting)

For questions or issues:
1. Check logs: `/var/snap/aws-iot-greengrass/common/greengrass/v2/logs/greengrass.log`
2. Verify certificates exist and are readable
3. Validate bootstrap configuration
4. Check AWS IoT Core for provisioning errors
5. Review CloudWatch logs for detailed errors
