# test_endpoint.py

import boto3
import json
import base64
import os
import logging
import pyaudio
import wave
from datetime import datetime
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # Common rate for speech recognition
        self.frames = []
        self.p = pyaudio.PyAudio()

    def record_audio(self, duration):
        """Record audio from microphone for specified duration"""
        logger.info(f"Recording for {duration} seconds...")
        
        stream = self.p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)

        self.frames = []
        
        # Calculate number of chunks to record
        for i in range(0, int(self.RATE / self.CHUNK * duration)):
            data = stream.read(self.CHUNK)
            self.frames.append(data)
            # Print progress
            if i % 10 == 0:
                seconds_left = duration - (i * self.CHUNK / self.RATE)
                print(f"\rRecording... {seconds_left:.1f} seconds left", end='')

        print("\nRecording finished!")
        stream.stop_stream()
        stream.close()

    def save_recording(self, filename):
        """Save the recorded audio to a WAV file"""
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        logger.info(f"Recording saved to {filename}")

    def cleanup(self):
        """Cleanup PyAudio"""
        self.p.terminate()

def encode_audio(audio_path):
    """Encode audio file to base64"""
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()
            return base64.b64encode(audio_content).decode('utf-8')
    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_path}")
        raise
    except Exception as e:
        logger.error(f"Error encoding audio: {str(e)}")
        raise

def test_endpoint(endpoint_name, audio_path):
    """Test the deployed endpoint with an audio file"""
    if not os.path.exists(audio_path):
        logger.error(f"Audio file does not exist: {audio_path}")
        return None

    try:
        runtime_client = boto3.client('sagemaker-runtime', region_name='ap-south-1')
        
        logger.info(f"Reading audio file: {audio_path}")
        # Read the audio file as binary
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        # Encode to base64
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')
        
        # Prepare request
        input_data = {
            "audio": encoded_audio
        }
        
        logger.info(f"Sending request to endpoint: {endpoint_name}")
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(input_data)
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode())
        
        # Check for error in response
        if 'error' in result:
            logger.error(f"Error from endpoint: {result['error']}")
            return None
            
        return result
        
    except boto3.exceptions.ClientError as e:
        logger.error(f"AWS Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def record_and_test():
    """Record audio from microphone and test the endpoint"""
    # Create recordings directory if it doesn't exist
    recordings_dir = "recordings"
    os.makedirs(recordings_dir, exist_ok=True)

    # Initialize recorder
    recorder = AudioRecorder()
    
    try:
        # Get recording duration from user
        duration = float(input("Enter recording duration in seconds (e.g., 5): "))
        
        # Record audio
        recorder.record_audio(duration)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = os.path.join(recordings_dir, f"recording_{timestamp}.wav")
        
        # Save recording
        recorder.save_recording(audio_file)
        
        # print(f"\nRecording saved to: {audio_file}")
        
        # Test endpoint with recording
        print("\nSending to transcription service...")
        result = test_endpoint(ENDPOINT_NAME, audio_file)
        
        return result, audio_file
        
    except Exception as e:
        logger.error(f"Error in recording: {str(e)}")
        return None, None
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    ENDPOINT_NAME = "indicasr-odia-endpoint"
    
    while True:
        print("\nChoose input method:")
        print("1. Record from microphone")
        print("2. Use existing audio file")
        print("3. Exit")
        choice = input("Enter your choice (1, 2, or 3): ")
        
        if choice == "1":
            result, audio_file = record_and_test()
            if result:
                print("\nTranscription Results:")
                print("--------------------")
                print(f"Transcription: {result.get('transcription', 'No transcription found')}")
                print("--------------------")
        
        elif choice == "2":
            TEST_AUDIO_PATH = input("Enter the path to your audio file: ")
            if os.path.exists(TEST_AUDIO_PATH):
                result = test_endpoint(ENDPOINT_NAME, TEST_AUDIO_PATH)
                if result:
                    print("\nTranscription Results:")
                    print("--------------------")
                    print(f"Transcription: {result.get('transcription', 'No transcription found')}")
                    print("--------------------")
            else:
                logger.error("Audio file not found")
        
        elif choice == "3":
            print("Exiting...")
            break
        
        else:
            logger.error("Invalid choice")