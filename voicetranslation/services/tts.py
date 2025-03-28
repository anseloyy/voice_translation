"""
Text-to-Speech Service

This module provides the service interface for text-to-speech functionality
"""
import logging
from models.tts import TextToSpeech

# Set up logging
logger = logging.getLogger(__name__)

# Global instance
_tts = None

def initialize():
    """Initialize the text-to-speech service"""
    global _tts
    
    logger.info("Initializing text-to-speech service")
    _tts = TextToSpeech()
    logger.info("Text-to-speech service initialized")

def get_tts():
    """Get the text-to-speech instance"""
    global _tts
    if _tts is None:
        initialize()
    return _tts

def speak_text(text, language='en'):
    """
    Convert text to speech
    
    Args:
        text (str): Text to convert to speech
        language (str): Language code for the voice
        
    Returns:
        str: Base64-encoded audio data
    """
    tts = get_tts()
    return tts.speak(text, language)

def get_supported_languages():
    """
    Get supported languages for text-to-speech
    
    Returns:
        list: List of supported language codes
    """
    tts = get_tts()
    return tts.get_supported_languages()