#!/bin/bash

# deploy.sh for Amazon Linux 2023 EC2
set -e

# Configuration
ACCOUNT_ID="339712730235"
REGION="ap-south-1"
REPOSITORY_NAME="indicasr-hindi"
IMAGE_TAG="latest"

# Print configuration
echo "=== Configuration ==="
echo "AWS Account ID: $ACCOUNT_ID"
echo "AWS Region: $REGION"
echo "Repository Name: $REPOSITORY_NAME"
echo "Image Tag: $IMAGE_TAG"
echo "===================="

# Ensure running on Amazon Linux 2023
if ! grep -q 'Amazon Linux 2023' /etc/os-release; then
    echo "Warning: This script is optimized for Amazon Linux 2023"
fi

# Check Docker service
if ! systemctl is-active --quiet docker; then
    echo "Docker service is not running. Starting Docker..."
    sudo systemctl start docker
fi

# Create ECR repository if it doesn't exist
echo "Creating ECR repository (if it doesn't exist)..."
if ! aws ecr describe-repositories --repository-names ${REPOSITORY_NAME} &> /dev/null; then
    echo "Creating new ECR repository: ${REPOSITORY_NAME}"
    aws ecr create-repository --repository-name ${REPOSITORY_NAME}
fi

# Get ECR login token and login to Docker
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Clean up any existing images
echo "Cleaning up existing images..."
docker rmi -f ${REPOSITORY_NAME}:${IMAGE_TAG} 2>/dev/null || true
docker rmi -f ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG} 2>/dev/null || true

# Build the Docker image
echo "Building Docker image..."
docker build --no-cache \
    --progress=plain \
    -t ${REPOSITORY_NAME}:${IMAGE_TAG} .

# Tag the image
echo "Tagging Docker image..."
docker tag ${REPOSITORY_NAME}:${IMAGE_TAG} ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}

# Push the image to ECR
echo "Pushing image to ECR..."
docker push ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}

# Verify the push
echo "Verifying image in ECR..."
aws ecr describe-images --repository-name ${REPOSITORY_NAME} --image-ids imageTag=${IMAGE_TAG}

# Clean up local images
echo "Cleaning up local images..."
docker rmi ${REPOSITORY_NAME}:${IMAGE_TAG} || true
docker rmi ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG} || true

echo "=== Deployment Complete ==="
echo "Image URI: ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}"

# Print next steps
echo ""
echo "Next steps:"
echo "1. Use this image URI in your SageMaker deployment script"
echo "2. Run the SageMaker deployment script: python3 deploy_sagemaker.py"
echo ""

# Print system information
echo "=== System Information ==="
echo "Docker version: $(docker --version)"
echo "AWS CLI version: $(aws --version)"
echo "System: $(uname -a)"
echo "======================="