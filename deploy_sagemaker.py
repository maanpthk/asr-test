# deploy_sagemaker.py

import boto3
import sagemaker
import json
import base64
from sagemaker import get_execution_role
import time

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
    try:
        role = get_execution_role()
    except Exception:
        # If running outside of SageMaker, create role ARN manually
        role = f'arn:aws:iam::{ACCOUNT_ID}:role/service-role/AmazonSageMaker-ExecutionRole-20240101T123456'  # Replace with your SageMaker execution role ARN
    
   
    
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
    return endpoint_name

def test_endpoint(endpoint_name, audio_path):
    """Test the deployed endpoint with an audio file"""
    def encode_audio(audio_path):
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()
            return base64.b64encode(audio_content).decode('utf-8')
    
    try:
        # Initialize SageMaker runtime client
        runtime_client = boto3.client('sagemaker-runtime')
        
        # Prepare test data
        input_data = {
            "audio": encode_audio(audio_path)
        }
        
        # Make inference request
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(input_data)
        )
        
        # Get results
        result = json.loads(response['Body'].read().decode())
        print("Transcription result:", result['transcription'])
        return result
        
    except Exception as e:
        print(f"Error testing endpoint: {str(e)}")
        return None

def cleanup_resources(endpoint_name):
    """Clean up SageMaker resources"""
    try:
        sagemaker_client = boto3.client('sagemaker')
        
        print(f"Deleting endpoint {endpoint_name}...")
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        
        print("Deleting endpoint configuration...")
        sagemaker_client.delete_endpoint_config(
            EndpointConfigName="indicasr-hindi-config"
        )
        
        print("Deleting model...")
        sagemaker_client.delete_model(ModelName="indicasr-hindi-model")
        
        print("Cleanup completed successfully!")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    # Deploy the model
    endpoint_name = deploy_model()
    
    if endpoint_name:
        # Test the endpoint with an audio file
        test_audio_path = "path/to/your/test.wav"  # Replace with your test audio file path
        test_result = test_endpoint(endpoint_name, test_audio_path)
        
        # Optional: Clean up resources
        cleanup_input = input("Do you want to clean up the SageMaker resources? (yes/no): ")
        if cleanup_input.lower() == 'yes':
            cleanup_resources(endpoint_name)