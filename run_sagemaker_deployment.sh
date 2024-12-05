#!/bin/bash
# run_sagemaker_deployment.sh

# Exit on error
set -e

# Check if role_arn.txt exists
if [ ! -f "role_arn.txt" ]; then
    echo "Error: role_arn.txt not found. Please run create_role.sh first."
    exit 1
fi

# Read the role ARN
ROLE_ARN=$(cat role_arn.txt)

# Create updated deploy_sagemaker.py with the correct role ARN
cat << EOF > deploy_sagemaker.py
# deploy_sagemaker.py

import boto3
import sagemaker
from sagemaker import get_execution_role

def deploy_model():
    # Initialize SageMaker session with explicit region
    session = boto3.Session(region_name='ap-south-1')
    sagemaker_session = sagemaker.Session(boto_session=session)
    
    # Configuration
    ACCOUNT_ID = '339712730235'
    REGION = 'ap-south-1'
    model_name = "indicasr-hindi-model"
    endpoint_config_name = "indicasr-hindi-config"
    endpoint_name = "indicasr-hindi-endpoint"
    
    # Use the role ARN from create_role.sh
    role = '${ROLE_ARN}'
    
    # Create SageMaker client with explicit region
    sagemaker_client = session.client('sagemaker')
    
    # Define container
    container = f"{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/indicasr-hindi:latest"
    
    print("Creating model...")
    try:
        response = sagemaker_client.create_model(
            ModelName=model_name,
            ExecutionRoleArn=role,
            PrimaryContainer={
                'Image': container
            }
        )
    except Exception as e:
        print(f"Error creating model: {str(e)}")
        return
    
    print("Creating endpoint configuration...")
    try:
        response = sagemaker_client.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[
                {
                    'VariantName': 'AllTraffic',
                    'ModelName': model_name,
                    'InstanceType': 'ml.g4dn.xlarge',
                    'InitialInstanceCount': 1
                }
            ]
        )
    except Exception as e:
        print(f"Error creating endpoint config: {str(e)}")
        return
    
    print("Creating endpoint (this may take several minutes)...")
    try:
        response = sagemaker_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        
        # Wait for endpoint to be ready
        waiter = sagemaker_client.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)
    except Exception as e:
        print(f"Error creating endpoint: {str(e)}")
        return
    
    print(f"Endpoint {endpoint_name} has been created successfully!")
    print(f"Endpoint Name: {endpoint_name}")
    return endpoint_name

if __name__ == "__main__":
    # Deploy the model
    endpoint_name = deploy_model()
EOF

# Install required Python packages
pip3 install boto3 sagemaker

# Run the deployment
echo "Running SageMaker deployment..."
python3 deploy_sagemaker.py