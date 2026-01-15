# Bootstrap Setup Documentation

Documentation for AWS IoT Greengrass fleet provisioning with claim certificates.

## Quick Links

- **[BOOTSTRAP-QUICKSTART.md](BOOTSTRAP-QUICKSTART.md)** - Get started in 5 minutes
- **[BOOTSTRAP-OVERVIEW.md](BOOTSTRAP-OVERVIEW.md)** - Understand the solution and architecture
- **[BOOTSTRAP-GUIDE.md](BOOTSTRAP-GUIDE.md)** - Complete implementation guide

## What to Read

### New to Bootstrap Setup?
Start with [BOOTSTRAP-OVERVIEW.md](BOOTSTRAP-OVERVIEW.md) to understand:
- What bootstrap setup is
- How it works
- When to use it vs interactive setup
- Architecture and security model

### Ready to Deploy?
Follow [BOOTSTRAP-QUICKSTART.md](BOOTSTRAP-QUICKSTART.md) for:
- Quick setup steps
- Essential commands
- Basic troubleshooting

### Need Detailed Instructions?
See [BOOTSTRAP-GUIDE.md](BOOTSTRAP-GUIDE.md) for:
- Complete AWS account setup
- Device preparation steps
- Device name strategies
- Production deployment checklist
- Comprehensive troubleshooting
- Security and maintenance

## Files in This Repository

### Scripts
- `amd64/local-scripts/iot-greengrass-bootstrap.py` - Basic bootstrap script
- `amd64/local-scripts/iot-greengrass-bootstrap-enhanced.py` - Enhanced with auto-detection
- `setup/create-claim-certificates.sh` - AWS setup helper

### Configuration Templates
- `amd64/bootstrap-config.yaml` - Device configuration template
- `setup/provisioning-template.json` - AWS IoT provisioning template
- `setup/device-policy.json` - IoT policy for devices
- `setup/trust-policy.json` - IAM trust policy
