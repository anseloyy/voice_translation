# Multilingual Voice-to-Text Translation System
## Setup Guide for Raspberry Pi 5

This guide will walk you through setting up the multilingual voice-to-text translation system with AI assistant on your Raspberry Pi 5.

## Hardware Requirements

- Raspberry Pi 5 (preferably with at least 4GB RAM)
- MicroSD card (32GB+ recommended)
- Microphone (USB or HAT-based)
- Speakers or headphones
- Optional: GPIO buttons and motion sensor (for kiosk mode)

## Software Setup

### 1. Basic Setup

Ensure your Raspberry Pi has the latest OS and needed dependencies:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev git cmake build-essential
```

### 2. Create a Project Directory and Clone or Transfer Files

```bash
mkdir voice_translation
cd voice_translation
# Either clone from your repository or transfer the files
```

### 3. Install Required Python Libraries

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install the core requirements
pip install flask flask-socketio flask-sqlalchemy gunicorn psycopg2-binary email-validator

# Install AI/ML related packages
pip install numpy scikit-learn
```

### 4. Install Speech Recognition Libraries

```bash
# Install Vosk for offline speech recognition
pip install vosk

# Download the Vosk models
mkdir -p models/vosk
# Download English model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/vosk/
mv models/vosk/vosk-model-small-en-us-0.15 models/vosk/vosk-model-small-en-us

# Download Filipino model
wget https://alphacephei.com/vosk/models/vosk-model-tl-ph-generic-0.6.zip
unzip vosk-model-tl-ph-generic-0.6.zip -d models/vosk/
mv models/vosk/vosk-model-tl-ph-generic-0.6 models/vosk/vosk-model-tl-ph

# Download Korean model
wget https://alphacephei.com/vosk/models/vosk-model-ko-0.22.zip
unzip vosk-model-ko-0.22.zip -d models/vosk/
mv models/vosk/vosk-model-ko-0.22 models/vosk/vosk-model-ko-kr
```

### 5. Install Language Detection

```bash
# Install FastText for language detection
pip install fasttext

# Download the language identification model
mkdir -p models/fasttext
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin -O models/fasttext/lid.176.bin
```

### 6. Install Translation Libraries

```bash
# Install offline translation libraries
pip install argostranslate

# The application will download the necessary translation models on startup
mkdir -p models/argos
```

### 7. Install Text-to-Speech

```bash
# Install Piper TTS
pip install piper-tts

# Create directories for Piper models
mkdir -p models/piper/en
mkdir -p models/piper/tl
mkdir -p models/piper/ko

# Download the specific ONNX models you mentioned
# English voice
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/vits/medium/en_US-lessac-medium.onnx -O models/piper/en/en_model.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/vits/medium/en_US-lessac-medium.onnx.json -O models/piper/en/en_config.json

# Spanish voice (for Filipino)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/vits/medium/es_ES-davefx-medium.onnx -O models/piper/tl/tl_model.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/vits/medium/es_ES-davefx-medium.onnx.json -O models/piper/tl/tl_config.json

# Vietnamese voice (for Korean)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vits/medium/vi_VN-vais1000-medium.onnx -O models/piper/ko/ko_model.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vits/medium/vi_VN-vais1000-medium.onnx.json -O models/piper/ko/ko_config.json
```

### 8. Install AI Assistant Dependencies

```bash
# Install llama-cpp-python with BLAS for better performance
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python

# Create directory for the LLM model
mkdir -p models/llm
```

### 9. Download the Mistral-7B-OpenOrca Model

```bash
# Download the Mistral 7B OpenOrca GGUF model (Q4_K_M version)
wget https://huggingface.co/TheBloke/Mistral-7B-OpenOrca-GGUF/resolve/main/mistral-7b-openorca.Q4_K_M.gguf -O models/llm/mistral-7b-openorca-Q_4_K_M.gguf
```

### 10. Setup Hardware Integration (optional)

If you're using the GPIO pins for hardware buttons and motion sensor:

```bash
# Install GPIO libraries
pip install RPi.GPIO
```

## Running the Application

Start the server with:

```bash
# Run the application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

You can access the web interface by opening a browser and navigating to:
```
http://<raspberry-pi-ip-address>:5000
```

## Hardware Wiring (optional)

If you want to use the kiosk mode with physical buttons, connect them as follows:

1. **Microphone button**: Connect to GPIO 17 and ground
2. **Process button**: Connect to GPIO 27 and ground
3. **Mode button**: Connect to GPIO 22 and ground
4. **Source language button**: Connect to GPIO 23 and ground
5. **Target language button**: Connect to GPIO 24 and ground
6. **Motion sensor**: Connect to GPIO 18, +5V, and ground

## Troubleshooting

1. **Memory Issues**: If you encounter memory issues when running the LLM:
   - Reduce the number of threads in the AI assistant configuration
   - Try using a smaller model if needed

2. **Speech Recognition Issues**:
   - Make sure your microphone is properly connected and configured
   - Check the system volume levels
   - Try using a USB microphone if the built-in one is not working well

3. **Performance Issues**:
   - Ensure your Raspberry Pi has adequate cooling
   - Consider using a Raspberry Pi 5 with 8GB RAM for better performance
   - Use a high-quality SD card or SSD for storage

4. **GPU Acceleration**:
   - For better LLM performance, you can try building llama-cpp-python with GPU acceleration:
     ```
     CMAKE_ARGS="-DLLAMA_CUBLAS=ON" pip install llama-cpp-python --force-reinstall --upgrade
     ```
     Note: This requires setting up the appropriate CUDA environment first.

5. **Missing Models**:
   - If any models fail to download automatically, check your internet connection
   - You can manually download them following the links in this guide

## System Features

1. **Voice Recognition**: Supports English, Filipino, and Korean
2. **Translation**: Real-time translation between all supported languages
3. **Text-to-Speech**: Speaks translations and AI responses
4. **AI Assistant**: Responds to queries using the Mistral-7B-OpenOrca model
5. **Multiple Interfaces**: Web, mobile, and kiosk modes
6. **Hardware Integration**: Support for physical buttons and motion sensing on Raspberry Pi

## Recommended System Configuration

- Raspberry Pi 5 with 8GB RAM
- 64GB or larger microSD card (Class 10 or better)
- External USB microphone
- External speakers
- (Optional) Power button case with cooling fan