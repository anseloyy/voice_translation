"""
AI Assistant Service

This module provides the service interface for AI assistant functionality
"""
import logging
import threading
import sys
import os
from functools import wraps

from models.ai_assistant import AIAssistant
from models.translation import Translator
from models.tts import TextToSpeech

# Define run_in_thread decorator here to avoid import issues
def run_in_thread(func):
    """Decorator to run a function in a separate thread"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

# Set up logging
logger = logging.getLogger(__name__)

# Global instances
_ai_assistant = None
_translator = None
_tts = None

def initialize():
    """Initialize the AI assistant service"""
    global _ai_assistant, _translator, _tts
    
    logger.info("Initializing AI assistant service")
    
    # Initialize AI assistant
    _ai_assistant = AIAssistant()
    
    # Get instances of translator and TTS
    from services.translation import get_translator
    from services.tts import get_tts
    _translator = get_translator()
    _tts = get_tts()
    
    logger.info("AI assistant service initialized")

def get_ai_assistant():
    """Get the AI assistant instance"""
    global _ai_assistant
    if _ai_assistant is None:
        initialize()
    return _ai_assistant

def process_query(query_text, source_lang='auto', response_lang='en', callback=None):
    """
    Process a user query and generate a response
    
    Args:
        query_text (str): The user's query text
        source_lang (str): Source language code
        response_lang (str): Response language code
        callback (callable): Function to call with the response
        
    Returns:
        dict: Response data if callback is None, otherwise None
    """
    # Detect language if auto
    if source_lang == 'auto' and _translator:
        detected_lang = _translator.detect_language(query_text)
        if detected_lang:
            source_lang = detected_lang
    
    # Translate to English if needed
    if source_lang != 'en' and _translator:
        english_query = _translator.translate(query_text, from_lang=source_lang, to_lang='en')
    else:
        english_query = query_text
    
    # Process asynchronously if callback provided
    if callback:
        _process_query_async(english_query, source_lang, response_lang, callback)
        return None
    
    # Otherwise process synchronously
    return _process_query_sync(english_query, source_lang, response_lang)

@run_in_thread
def _process_query_async(english_query, source_lang, response_lang, callback):
    """Process query asynchronously and call callback with result"""
    result = _process_query_sync(english_query, source_lang, response_lang)
    callback(result)

def _process_query_sync(english_query, source_lang, response_lang):
    """Process query synchronously and return result"""
    try:
        # Get AI assistant
        ai_assistant = get_ai_assistant()
        
        # Generate response in English
        english_response = ai_assistant.generate_response(english_query, 'en')
        
        # Translate response if needed
        if response_lang != 'en' and _translator:
            translated_response = _translator.translate(english_response, 
                                                      from_lang='en', 
                                                      to_lang=response_lang)
        else:
            translated_response = english_response
        
        # Generate speech if TTS available
        audio_data = None
        if _tts:
            try:
                audio_data = _tts.speak(translated_response, response_lang)
            except Exception as e:
                logger.error(f"TTS error: {str(e)}")
        
        # Return response data
        return {
            'text': translated_response,
            'audio': audio_data,
            'source_language': source_lang,
            'target_language': response_lang
        }
        
    except Exception as e:
        logger.error(f"Error processing AI assistant query: {str(e)}")
        error_messages = {
            'en': "I'm sorry, I couldn't process your request.",
            'tl': "Paumanhin, hindi ko maproseso ang iyong kahilingan.",
            'ko': "죄송합니다, 요청을 처리할 수 없습니다."
        }
        error_msg = error_messages.get(response_lang, error_messages['en'])
        
        return {
            'text': error_msg,
            'audio': None,
            'source_language': source_lang,
            'target_language': response_lang,
            'error': str(e)
        }

def is_available():
    """Check if AI assistant is available"""
    ai_assistant = get_ai_assistant()
    return ai_assistant.is_available()