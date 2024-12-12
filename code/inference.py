# updated inference.py

import os
import json
import torch
import nemo.collections.asr as nemo_asr
from flask import Flask, request, jsonify
import logging
import base64
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

model = None

def model_fn(model_dir):
    """Load the model for inference"""
    try:
        logger.info(f"Loading model from directory: {model_dir}")
        model_path = os.path.join(model_dir, "ai4b_indicConformer_or.nemo")
        tokenizer_dir = os.path.join(model_dir, "tokenizer")
        
        # Check if files exist
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        if not os.path.exists(tokenizer_dir):
            raise FileNotFoundError(f"Tokenizer directory not found at: {tokenizer_dir}")
            
        logger.info(f"Model file exists at: {model_path}")
        logger.info(f"Tokenizer directory exists at: {tokenizer_dir}")
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")
        
        # Load model with tokenizer configuration
        model = nemo_asr.models.EncDecCTCModelBPE.restore_from(
            restore_path=model_path,
            override_config_path={
                "tokenizer": {
                    "dir": tokenizer_dir
                }
            }
        )
        model.to(device)
        model.eval()
        
        return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        logger.error(f"Stack trace: ", exc_info=True)
        raise

def input_fn(request_body, request_content_type):
    """Deserialize and prepare the prediction input"""
    logger.info(f"Received request with content type: {request_content_type}")
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        logger.info(f"Processed input data: {input_data}")
        return input_data
    else:
        error_msg = f"Unsupported content type: {request_content_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# inference.py
def predict_fn(input_data, model):
    """Make prediction using the input data and loaded model"""
    try:
        logger.info("Starting prediction")
        
        # Decode base64 to audio file
        audio_data = base64.b64decode(input_data['audio'])
        
        # Save to temporary file
        temp_file = '/tmp/temp_audio.wav'
        with open(temp_file, 'wb') as f:
            f.write(audio_data)
        
        # Make prediction
        transcription = model.transcribe([temp_file])
        
        # Clean up
        os.remove(temp_file)
        
        logger.info(f"Prediction completed: {transcription[0]}")
        return transcription[0]
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {"error": str(e)}

def output_fn(prediction, content_type):
    """Serialize and return the prediction output"""
    logger.info(f"Formatting output with content type: {content_type}")
    if content_type == "application/json":
        return json.dumps({"transcription": prediction})
    error_msg = f"Unsupported content type: {content_type}"
    logger.error(error_msg)
    raise ValueError(error_msg)

@app.route('/ping', methods=['GET'])
def ping():
    logger.info("Health check ping received")
    return jsonify({"status": "healthy"})

@app.route('/inference', methods=['POST'])
def inference():
    logger.info("Received inference request")
    global model
    if model is None:
        model = model_fn("/opt/ml/model")
        logger.info("Model loaded successfully!")
    
    content = request.json
    prediction = predict_fn(content, model)
    return jsonify(output_fn(prediction, "application/json"))

@app.route('/invocations', methods=['POST'])
def invocations():
    logger.info("Received SageMaker invocation request")
    global model
    if model is None:
        model = model_fn("/opt/ml/model")
        logger.info("Model loaded successfully!")
    
    if request.content_type != 'application/json':
        error_msg = 'Content type must be application/json'
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 415
    
    try:
        content = input_fn(request.get_data().decode('utf-8'), request.content_type)
        prediction = predict_fn(content, model)
        return output_fn(prediction, "application/json")
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == "__main__":
    # Print CUDA information
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info(f"CUDA version: {torch.version.cuda}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    app.run(host='0.0.0.0', port=8080)