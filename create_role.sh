#!/bin/bash
# create_role.sh

# Exit on error
set -e

# Configuration
ACCOUNT_ID="339712730235"
ROLE_NAME="SageMaker-ExecutionRole"

echo "=== Creating IAM Role for SageMaker ==="

# Create trust policy document
cat << EOF > trust-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "sagemaker.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create custom policy document
cat << EOF > sagemaker-custom-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:*",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "cloudwatch:PutMetricData",
                "s3:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create the role
echo "Creating IAM role..."
aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document file://trust-policy.json

# Create and attach custom policy
echo "Creating and attaching custom policy..."
POLICY_ARN=$(aws iam create-policy \
    --policy-name SageMaker-CustomPolicy \
    --policy-document file://sagemaker-custom-policy.json \
    --query 'Policy.Arn' \
    --output text)

# Attach policies
echo "Attaching policies..."
aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

# Get and save the role ARN
ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --query 'Role.Arn' --output text)
echo ${ROLE_ARN} > role_arn.txt

echo "=== Role Creation Complete ==="
echo "Role ARN: ${ROLE_ARN}"
echo "Role ARN has been saved to role_arn.txt"

# Cleanup JSON files
rm -f trust-policy.json sagemaker-custom-policy.json