"""
Speech Recognition Module

This module handles speech-to-text conversion using Vosk for offline recognition
"""

import os
import logging
import json
import tempfile
import urllib.request
import zipfile
import shutil
import threading
import queue
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """Class for performing speech recognition using Vosk"""
    
    def __init__(self):
        """Initialize the speech recognizer"""
        self.vosk_available = self._check_vosk_available()
        self.model_paths = {}
        self.models = {}
        self.recognizers = {}
        self.recognition_queue = queue.Queue()
        self.supported_languages = ['en', 'tl', 'ko']
        
        # Start with downloading English model
        if self.vosk_available:
            self._download_model('en')
            
            # Start a thread for handling the recognition queue
            threading.Thread(target=self._recognition_worker, daemon=True).start()
    
    def _check_vosk_available(self):
        """Check if Vosk is available"""
        try:
            import vosk
            self.vosk = vosk
            logger.info("Vosk library available")
            return True
        except ImportError:
            logger.warning("Vosk library not available. Speech recognition will be limited.")
            return False
    
    def _download_model(self, language):
        """
        Download Vosk model for the specified language
        
        Args:
            language (str): Language code ('en', 'tl', 'ko')
        """
        if not self.vosk_available:
            return
        
        # Define model URLs based on language
        model_urls = {
            'en': "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            'tl': "https://alphacephei.com/vosk/models/vosk-model-small-tl-ph-0.15.zip",
            'ko': "https://alphacephei.com/vosk/models/vosk-model-small-ko-0.22.zip"
        }
        
        if language not in model_urls:
            logger.error(f"No model URL defined for language: {language}")
            return
        
        url = model_urls[language]
        
        # Define models directory
        models_dir = Path(os.path.dirname(os.path.abspath(__file__)), "vosk_models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Define model path
        model_path = os.path.join(models_dir, f"vosk-model-{language}")
        self.model_paths[language] = model_path
        
        # Check if model already exists
        if os.path.exists(model_path):
            logger.info(f"Vosk model for {language} already exists at {model_path}")
            self._load_model(language)
            return
        
        # Download and extract model
        logger.info(f"Downloading Vosk model for {language}...")
        try:
            # Download to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_path = temp_file.name
            
            urllib.request.urlretrieve(url, temp_path)
            
            # Extract the model
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # Get the directory name from the zip
                zip_dir = zip_ref.namelist()[0].split('/')[0]
                
                # Extract to a temporary directory
                extract_dir = os.path.join(models_dir, "temp_extract")
                os.makedirs(extract_dir, exist_ok=True)
                zip_ref.extractall(extract_dir)
                
                # Move the extracted folder to the model path
                extracted_model_path = os.path.join(extract_dir, zip_dir)
                
                # Remove previous model if it exists
                if os.path.exists(model_path):
                    shutil.rmtree(model_path)
                
                # Move the extracted model to the final location
                shutil.move(extracted_model_path, model_path)
                
                # Clean up temp extraction directory
                shutil.rmtree(extract_dir)
            
            # Remove the temporary zip file
            os.unlink(temp_path)
            
            logger.info(f"Vosk model for {language} downloaded and extracted to {model_path}")
            
            # Load the model
            self._load_model(language)
            
        except Exception as e:
            logger.error(f"Failed to download and extract Vosk model for {language}: {e}")
    
    def _load_model(self, language):
        """
        Load the Vosk model for the specified language
        
        Args:
            language (str): Language code ('en', 'tl', 'ko')
        """
        if not self.vosk_available or language not in self.model_paths:
            return
        
        try:
            model_path = self.model_paths[language]
            self.models[language] = self.vosk.Model(model_path)
            logger.info(f"Vosk model for {language} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Vosk model for {language}: {e}")
    
    def recognize(self, audio_data, language='en', online=False):
        """
        Recognize speech from audio data
        
        Args:
            audio_data (bytes): Audio data in PCM format
            language (str): Language code ('en', 'tl', 'ko')
            online (bool): Whether to use online recognition if available
            
        Returns:
            str: Recognized text
        """
        # For online recognition (Google Speech Recognition)
        if online:
            try:
                return self._recognize_online(audio_data, language)
            except Exception as e:
                logger.error(f"Online speech recognition failed: {e}")
                logger.info("Falling back to offline recognition")
        
        # For offline recognition (Vosk)
        if not self.vosk_available:
            return "[Speech recognition unavailable]"
        
        # Make sure we have the model for this language
        if language not in self.models:
            self._download_model(language)
            
            # If still not available, use English as fallback
            if language not in self.models and 'en' in self.models:
                language = 'en'
            # If no models available, return error
            elif language not in self.models:
                return "[Speech recognition model not available]"
        
        try:
            # Create a recognizer if we don't have one for this language yet
            if language not in self.recognizers:
                self.recognizers[language] = self.vosk.KaldiRecognizer(self.models[language], 16000)
            
            recognizer = self.recognizers[language]
            
            # Process audio data
            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                return result.get('text', '')
            else:
                # Return partial result
                partial = json.loads(recognizer.PartialResult())
                return partial.get('partial', '')
                
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return "[Speech recognition error]"
    
    def _recognize_online(self, audio_data, language):
        """
        Perform online speech recognition using Google Speech Recognition
        
        Args:
            audio_data (bytes): Audio data in PCM format
            language (str): Language code ('en', 'tl', 'ko')
            
        Returns:
            str: Recognized text
        """
        # Map language codes to Google Speech Recognition format
        language_map = {
            'en': 'en-US',
            'tl': 'fil-PH',
            'ko': 'ko-KR'
        }
        
        google_lang = language_map.get(language, 'en-US')
        
        # Write audio data to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
            
            # Create a WAV file with the audio data
            # This is a simplified version - in a real app, proper WAV header would be needed
            temp_wav.write(audio_data)
        
        try:
            # Use Google's speech recognition API
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(temp_wav_path) as source:
                audio = recognizer.record(source)
                
            text = recognizer.recognize_google(audio, language=google_lang)
            return text
            
        except ImportError:
            logger.error("speech_recognition library not available")
            raise
        except Exception as e:
            logger.error(f"Google speech recognition error: {e}")
            raise
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_wav_path)
            except:
                pass
    
    def _recognition_worker(self):
        """Worker thread for processing speech recognition requests"""
        while True:
            try:
                # Get a recognition task from the queue
                task = self.recognition_queue.get()
                
                if task is None:  # Sentinel value to stop the worker
                    break
                
                audio_data, language, online, callback = task
                
                # Perform recognition
                result = self.recognize(audio_data, language, online)
                
                # Call the callback with the result
                if callback:
                    callback(result)
                    
            except Exception as e:
                logger.error(f"Error in recognition worker: {e}")
            finally:
                self.recognition_queue.task_done()
    
    def recognize_async(self, audio_data, language='en', online=False, callback=None):
        """
        Queue audio data for asynchronous recognition
        
        Args:
            audio_data (bytes): Audio data in PCM format
            language (str): Language code ('en', 'tl', 'ko')
            online (bool): Whether to use online recognition if available
            callback (callable): Function to call with the recognition result
        """
        self.recognition_queue.put((audio_data, language, online, callback))
    
    def get_supported_languages(self):
        """Get the list of supported languages"""
        return self.supported_languages
