"""
Text-to-Speech Module

This module handles text-to-speech conversion using Piper TTS
"""

import os
import logging
import tempfile
import urllib.request
import tarfile
import json
import base64
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class TextToSpeech:
    """Class for converting text to speech using Piper TTS"""
    
    def __init__(self):
        """Initialize the text-to-speech engine"""
        self.piper_available = self._check_piper_available()
        self.model_paths = {}
        self.supported_languages = ['en', 'tl', 'ko']
        self.voices = {}
        
        # Initialize models
        if self.piper_available:
            self._initialize_models()
    
    def _check_piper_available(self):
        """Check if Piper TTS is available"""
        try:
            # Check if piper executable exists
            result = subprocess.run(['which', 'piper'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                logger.info("Piper TTS found")
                return True
            else:
                logger.warning("Piper TTS not found in PATH. Text-to-speech functionality will be limited.")
                return False
        except Exception as e:
            logger.warning(f"Error checking for Piper TTS: {e}")
            return False
    
    def _initialize_models(self):
        """Initialize TTS models for each supported language"""
        if not self.piper_available:
            return
        
        # Define model URLs
        model_urls = {
            'en': "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/vits/medium/en_US-lessac-medium.onnx?download=true",
            'tl': "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/vits/medium/es_ES-davefx-medium.onnx?download=true",  # Spanish as substitute for Filipino
            'ko': "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vits/medium/vi_VN-vais1000-medium.onnx?download=true"  # Vietnamese as substitute for Korean
        }
        
        # Define models directory
        models_dir = Path(os.path.dirname(os.path.abspath(__file__)), "piper_models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Download models if needed
        for language, url in model_urls.items():
            lang_dir = os.path.join(models_dir, language)
            os.makedirs(lang_dir, exist_ok=True)
            
            model_path = os.path.join(lang_dir, f"{language}_model.onnx")
            config_path = os.path.join(lang_dir, f"{language}_config.json")
            
            # Save model paths
            self.model_paths[language] = {
                'model': model_path,
                'config': config_path
            }
            
            # Download model if not exists
            if not os.path.exists(model_path):
                try:
                    logger.info(f"Downloading Piper TTS model for {language}...")
                    
                    # Download to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    urllib.request.urlretrieve(url, temp_path)
                    
                    # Move to final location
                    os.rename(temp_path, model_path)
                    
                    logger.info(f"Piper TTS model for {language} downloaded successfully")
                    
                    # Create a simple config file
                    voice_config = {
                        "language": language,
                        "sample_rate": 22050,
                        "speaker_id": 0,
                        "length_scale": 1.0,
                        "noise_scale": 0.667,
                        "noise_w": 0.8
                    }
                    
                    with open(config_path, 'w') as f:
                        json.dump(voice_config, f)
                    
                except Exception as e:
                    logger.error(f"Failed to download Piper TTS model for {language}: {e}")
            else:
                logger.info(f"Piper TTS model for {language} already exists at {model_path}")
            
            # Register the voice
            self.voices[language] = {
                'name': f"{language}_voice",
                'model_path': model_path,
                'config_path': config_path
            }
    
    def speak(self, text, language='en'):
        """
        Convert text to speech
        
        Args:
            text (str): Text to convert to speech
            language (str): Language code ('en', 'tl', 'ko')
            
        Returns:
            str: Base64-encoded audio data
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for text-to-speech")
            return ""
        
        # Check if language is supported
        if language not in self.supported_languages:
            logger.warning(f"Language {language} not supported, falling back to English")
            language = 'en'
        
        # Check if Piper is available
        if not self.piper_available:
            logger.error("Piper TTS not available")
            return ""
        
        # Check if we have a model for this language
        if language not in self.voices:
            logger.warning(f"No TTS voice available for {language}, falling back to English")
            language = 'en'
            
            # If still no voice available, return error
            if language not in self.voices:
                logger.error("No TTS voices available")
                return ""
        
        try:
            # Create temporary files for input text and output audio
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as text_file:
                text_file_path = text_file.name
                text_file.write(text)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                audio_file_path = audio_file.name
            
            # Get voice data
            voice = self.voices[language]
            model_path = voice['model_path']
            
            # Run Piper TTS
            cmd = [
                'piper',
                '--model', model_path,
                '--output_file', audio_file_path,
                '--file', text_file_path
            ]
            
            logger.debug(f"Running Piper TTS command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"Piper TTS error: {process.stderr}")
                return ""
            
            # Read the generated audio file
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Encode audio data as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            logger.info(f"Generated speech for text in {language}")
            
            # Clean up temporary files
            os.unlink(text_file_path)
            os.unlink(audio_file_path)
            
            return audio_base64
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return ""
    
    def get_supported_languages(self):
        """Get the list of supported languages"""
        return self.supported_languages
