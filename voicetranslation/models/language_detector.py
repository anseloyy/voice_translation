"""
Language Detector Module

This module detects the language of a given text using FastText
"""

import os
import logging
import tempfile
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Class for detecting languages using FastText"""
    
    def __init__(self):
        """Initialize the language detector"""
        self.model = None
        self.model_path = None
        self.supported_languages = ['en', 'tl', 'ko']
        
        # Try to initialize fastText
        try:
            import fasttext
            self.fasttext = fasttext
            self._initialize_model()
        except ImportError:
            logger.warning("FastText library not available. Language detection will use fallback methods.")
            self.fasttext = None
    
    def _initialize_model(self):
        """Initialize and load the FastText model"""
        if self.fasttext is None:
            return
        
        # Define model directory and path
        models_dir = Path(os.path.dirname(os.path.abspath(__file__)), "models")
        os.makedirs(models_dir, exist_ok=True)
        
        self.model_path = os.path.join(models_dir, "lid.176.bin")
        
        # Check if model exists, if not download it
        if not os.path.exists(self.model_path):
            logger.info("Downloading FastText language identification model...")
            try:
                # URL for the FastText language identification model
                url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
                
                # Download to a temporary file first
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = temp_file.name
                    
                urllib.request.urlretrieve(url, temp_path)
                
                # Move to final location
                os.rename(temp_path, self.model_path)
                logger.info(f"FastText model downloaded to {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to download FastText model: {e}")
                return
        
        # Load the model
        try:
            self.model = self.fasttext.load_model(self.model_path)
            logger.info("FastText language identification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load FastText model: {e}")
            self.model = None
    
    def detect(self, text):
        """
        Detect the language of the given text
        
        Args:
            text (str): The text to detect the language of
            
        Returns:
            str: ISO 639-1 language code ('en', 'tl', 'ko', etc.)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for language detection")
            return 'en'  # Default to English
        
        # Try FastText if available
        if self.model:
            try:
                # Get prediction from FastText
                predictions = self.model.predict(text.replace('\n', ' '))
                lang_code = predictions[0][0].replace('__label__', '')
                
                # Map some common language codes
                lang_mapping = {
                    'fil': 'tl',  # Filipino/Tagalog
                    'kor': 'ko',  # Korean
                    'eng': 'en'   # English
                }
                
                lang_code = lang_mapping.get(lang_code, lang_code)
                
                # If not in supported languages, fall back to English
                if lang_code not in self.supported_languages:
                    logger.warning(f"Detected language {lang_code} is not supported, falling back to English")
                    return 'en'
                
                logger.info(f"Detected language: {lang_code}")
                return lang_code
            
            except Exception as e:
                logger.error(f"Error in FastText language detection: {e}")
        
        # Fallback language detection method (simplified)
        logger.info("Using fallback language detection method")
        
        # Count character frequencies
        text = text.lower()
        
        # Korean characters (Hangul) range
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
        
        # Common Filipino words and characters
        filipino_words = ['ang', 'ng', 'mga', 'sa', 'at', 'ay', 'ko', 'mo', 'po', 'ito']
        filipino_count = sum(word in text.split() for word in filipino_words)
        
        # Calculate percentages
        text_len = max(1, len(text))
        korean_percentage = korean_chars / text_len
        
        if korean_percentage > 0.3:
            return 'ko'
        elif filipino_count >= 2:
            return 'tl'
        else:
            # Default to English
            return 'en'
    
    def get_supported_languages(self):
        """Get the list of supported languages"""
        return self.supported_languages
