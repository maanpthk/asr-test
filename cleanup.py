# cleanup.py
import boto3

def cleanup_failed_deployment():
    sagemaker = boto3.client('sagemaker', region_name='ap-south-1')
    
    try:
        # Delete endpoint
        print("Deleting endpoint...")
        sagemaker.delete_endpoint(EndpointName='indicasr-hindi-endpoint')
    except Exception as e:
        print(f"Error deleting endpoint: {e}")
    
    try:
        # Delete endpoint config
        print("Deleting endpoint configuration...")
        sagemaker.delete_endpoint_config(EndpointConfigName='indicasr-hindi-config')
    except Exception as e:
        print(f"Error deleting endpoint config: {e}")
    
    try:
        # Delete model
        print("Deleting model...")
        sagemaker.delete_model(ModelName='indicasr-hindi-model')
    except Exception as e:
        print(f"Error deleting model: {e}")

if __name__ == "__main__":
    cleanup_failed_deployment()