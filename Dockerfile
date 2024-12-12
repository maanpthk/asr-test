# Use a newer base image with Python 3.8
FROM python:3.8-slim

# Install system dependencies including CUDA
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    gcc \
    g++ \
    make \
    python3-dev \
    git \
    tzdata \
    curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/ml/code

# Upgrade pip and install basic packages
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch with CUDA support first
RUN pip3 install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113

# Install other requirements including Flask
COPY code/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /opt/ml/model/tokenizer

# Copy model files
COPY model/ai4b_indicConformer_or.nemo /opt/ml/model/
COPY model/tokenizer/ /opt/ml/model/tokenizer/

# Verify model and tokenizer files
RUN ls -la /opt/ml/model/ && \
    ls -la /opt/ml/model/tokenizer/ && \
    echo "Model and tokenizer files copied successfully!"

# Copy inference code
COPY code/inference.py .

# Set environment variables
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/ml/code:${PATH}"

# Add these lines before the entrypoint
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Print environment information during build
RUN python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda); print('PyTorch version:', torch.__version__)"

# Create directory for temporary files
RUN mkdir -p /tmp && chmod 777 /tmp

# Set Python unbuffered output
ENV PYTHONUNBUFFERED=1

# Set permissions
RUN chmod -R 755 /opt/ml/code && \
    chmod -R 755 /opt/ml/model

# Log directory structure
RUN echo "=== Directory Structure ===" && \
    ls -R /opt/ml && \
    echo "=========================="

# Verify CUDA installation
RUN if [ -x "$(command -v nvidia-smi)" ]; then \
        nvidia-smi; \
    else \
        echo "NVIDIA driver not installed (this is normal for build environment)"; \
    fi

# Set the entry point
ENTRYPOINT ["python3", "inference.py"]

# Add labels
LABEL maintainer="your-email@example.com" \
      model="indicasr-odia" \
      version="1.0" \
      description="Indic ASR Odia Model Container"