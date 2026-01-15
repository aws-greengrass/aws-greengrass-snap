#!/bin/bash
# Helper script to create claim certificates for fleet provisioning
# Run this on your development machine (not on the device)

set -e

echo "=========================================="
echo "AWS IoT Fleet Provisioning Setup Helper"
echo "=========================================="
echo ""

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Get AWS region
read -p "Enter AWS Region (e.g., us-east-1): " AWS_REGION
if [ -z "$AWS_REGION" ]; then
    echo "Error: AWS Region is required"
    exit 1
fi

# Get provisioning template name
read -p "Enter Provisioning Template Name (default: GreengrassFleetProvisioningTemplate): " TEMPLATE_NAME
TEMPLATE_NAME=${TEMPLATE_NAME:-GreengrassFleetProvisioningTemplate}

# Create output directory
OUTPUT_DIR="./claim-certificates"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "Step 1: Creating claim certificate..."
CERT_OUTPUT=$(aws iot create-keys-and-certificate \
    --set-as-active \
    --certificate-pem-outfile "$OUTPUT_DIR/claim.cert.pem" \
    --public-key-outfile "$OUTPUT_DIR/claim.public.key" \
    --private-key-outfile "$OUTPUT_DIR/claim.private.key" \
    --region "$AWS_REGION" \
    --output json)

CERT_ARN=$(echo "$CERT_OUTPUT" | grep -o '"certificateArn": "[^"]*' | cut -d'"' -f4)
CERT_ID=$(echo "$CERT_OUTPUT" | grep -o '"certificateId": "[^"]*' | cut -d'"' -f4)

echo "[OK] Claim certificate created"
echo "  Certificate ID: $CERT_ID"
echo "  Certificate ARN: $CERT_ARN"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo ""
echo "Step 2: Creating claim policy..."

# Create claim policy document
cat > "$OUTPUT_DIR/claim-policy.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Connect"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Publish", "iot:Receive"],
      "Resource": [
        "arn:aws:iot:${AWS_REGION}:${ACCOUNT_ID}:topic/\$aws/certificates/create/*",
        "arn:aws:iot:${AWS_REGION}:${ACCOUNT_ID}:topic/\$aws/provisioning-templates/${TEMPLATE_NAME}/provision/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["iot:Subscribe"],
      "Resource": [
        "arn:aws:iot:${AWS_REGION}:${ACCOUNT_ID}:topicfilter/\$aws/certificates/create/*",
        "arn:aws:iot:${AWS_REGION}:${ACCOUNT_ID}:topicfilter/\$aws/provisioning-templates/${TEMPLATE_NAME}/provision/*"
      ]
    }
  ]
}
EOF

POLICY_NAME="GreengrassClaimPolicy-$(date +%s)"
aws iot create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://"$OUTPUT_DIR/claim-policy.json" \
    --region "$AWS_REGION" > /dev/null

echo "[OK] Claim policy created: $POLICY_NAME"

echo ""
echo "Step 3: Attaching policy to certificate..."
aws iot attach-policy \
    --policy-name "$POLICY_NAME" \
    --target "$CERT_ARN" \
    --region "$AWS_REGION"

echo "[OK] Policy attached to certificate"

# Get IoT endpoints
echo ""
echo "Step 4: Getting IoT endpoints..."
IOT_DATA_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --region "$AWS_REGION" --query endpointAddress --output text)
IOT_CRED_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:CredentialProvider --region "$AWS_REGION" --query endpointAddress --output text)

echo "[OK] IoT Data Endpoint: $IOT_DATA_ENDPOINT"
echo "[OK] IoT Cred Endpoint: $IOT_CRED_ENDPOINT"

# Create bootstrap config
echo ""
echo "Step 5: Creating bootstrap configuration..."
cat > "$OUTPUT_DIR/bootstrap-config.yaml" <<EOF
# AWS IoT Greengrass Bootstrap Configuration
# Generated on $(date)

awsRegion: "$AWS_REGION"
deviceName: "PROMPT"
serialNumber: ""
provisioningTemplate: "$TEMPLATE_NAME"
iotDataEndpoint: "$IOT_DATA_ENDPOINT"
iotCredEndpoint: "$IOT_CRED_ENDPOINT"
iotRoleAlias: "GreengrassV2TokenExchangeRoleAlias"
nucleusVersion: "2.16.0"
claimCertificatePath: "/var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem"
claimPrivateKeyPath: "/var/snap/aws-iot-greengrass/common/claim-certs/claim.private.key"
EOF

echo "[OK] Bootstrap configuration created"

# Create README
cat > "$OUTPUT_DIR/README.txt" <<EOF
Claim Certificates for AWS IoT Greengrass Fleet Provisioning
Generated on $(date)

Certificate ID: $CERT_ID
Certificate ARN: $CERT_ARN
Policy Name: $POLICY_NAME
AWS Region: $AWS_REGION
Provisioning Template: $TEMPLATE_NAME

Files in this directory:
- claim.cert.pem: Claim certificate (copy to device)
- claim.private.key: Claim private key (copy to device)
- claim.public.key: Public key (not needed on device)
- claim-policy.json: Policy document (for reference)
- bootstrap-config.yaml: Bootstrap configuration (copy to device)

Device Setup Instructions:
1. Copy claim.cert.pem and claim.private.key to device:
   /var/snap/aws-iot-greengrass/common/claim-certs/

2. Copy bootstrap-config.yaml to device:
   /var/snap/aws-iot-greengrass/common/bootstrap-config.yaml

3. Set permissions:
   sudo chmod 644 /var/snap/aws-iot-greengrass/common/claim-certs/claim.cert.pem
   sudo chmod 600 /var/snap/aws-iot-greengrass/common/claim-certs/claim.private.key

4. Run bootstrap setup:
   sudo aws-iot-greengrass.bootstrap

IMPORTANT: Keep these files secure! The claim certificate can be used to
provision devices in your AWS account.
EOF

echo ""
echo "=========================================="
echo "[OK] Setup Complete!"
echo "=========================================="
echo ""
echo "Files created in: $OUTPUT_DIR/"
echo ""
echo "Next steps:"
echo "1. Review the files in $OUTPUT_DIR/"
echo "2. Copy claim certificates and config to your devices"
echo "3. Ensure provisioning template '$TEMPLATE_NAME' exists in AWS"
echo "4. Run 'aws-iot-greengrass.bootstrap' on each device"
echo ""
echo "For detailed instructions, see docs/BOOTSTRAP-GUIDE.md"
