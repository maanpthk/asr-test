# test_endpoint.py

import boto3
import json
import base64

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

if __name__ == "__main__":
    # Replace these values with your endpoint name and test audio file
    ENDPOINT_NAME = "indicasr-hindi-endpoint"
    TEST_AUDIO_PATH = "path/to/your/test.wav"
    
    test_endpoint(ENDPOINT_NAME, TEST_AUDIO_PATH)