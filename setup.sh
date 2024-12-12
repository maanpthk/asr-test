#!/bin/bash
# setup.sh

set -e  # Exit on error

echo "=== Starting Setup ==="

# 1. Create model directory
echo "Creating model directory..."
mkdir -p model

# 2. Download model
echo "Downloading model..."
curl -L "https://objectstore.e2enetworks.net/indic-asr-public/indicConformer/ai4b%5FindicConformer%5For.nemo" -o model/ai4b_indicConformer_or.nemo

# 3. Install requirements and extract tokenizer
echo "Installing requirements for tokenizer extraction..."
pip install nemo_toolkit[all]

echo "Extracting tokenizer..."
python extract_tokenizer.py

# 4. Verify files
echo "Verifying files..."
if [ ! -f "model/ai4b_indicConformer_or.nemo" ]; then
    echo "Error: Model file not found!"
    exit 1
fi

if [ ! -d "model/tokenizer" ]; then
    echo "Error: Tokenizer directory not found!"
    exit 1
fi

# 5. Run deployment scripts
echo "Running deployment scripts..."
./deploy.sh
./run_sagemaker_deployment.sh

echo "=== Setup Complete ==="