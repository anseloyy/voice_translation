"""
Translation Service

This module provides the service interface for translation functionality
"""
import logging
from models.translation import Translator

# Set up logging
logger = logging.getLogger(__name__)

# Global instance
_translator = None

def initialize():
    """Initialize the translation service"""
    global _translator
    
    logger.info("Initializing translation service")
    _translator = Translator()
    logger.info("Translation service initialized")

def get_translator():
    """Get the translator instance"""
    global _translator
    if _translator is None:
        initialize()
    return _translator

def translate_text(text, from_lang='auto', to_lang='en', online=None):
    """
    Translate text from one language to another
    
    Args:
        text (str): Text to translate
        from_lang (str): Source language code
        to_lang (str): Target language code
        online (bool): Whether to use online translation if available
        
    Returns:
        str: Translated text
    """
    translator = get_translator()
    return translator.translate(text, from_lang, to_lang, online=online)

def detect_language(text):
    """
    Detect the language of text
    
    Args:
        text (str): Text to detect language from
        
    Returns:
        str: Detected language code
    """
    translator = get_translator()
    return translator.detect_language(text)

def get_supported_languages():
    """
    Get supported languages for translation
    
    Returns:
        list: List of supported language codes
    """
    translator = get_translator()
    return translator.get_supported_languages()