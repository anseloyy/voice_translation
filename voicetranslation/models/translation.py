"""
Translation Module

This module handles text translation using ArgosTranslate/LibreTranslate for offline 
translation and Google Translate for online translation
"""
import logging

# Set up logging
logger = logging.getLogger(__name__)

import os
import logging
import tempfile
import urllib.request
import zipfile
import shutil
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class Translator:
    """Class for translating text between different languages"""
    
    def __init__(self):
        """Initialize the translator"""
        self.argos_available = self._check_argos_available()
        self.translation_pairs = {}
        self.supported_languages = ['en', 'tl', 'ko']
        
        # Initialize translation pairs for offline use
        if self.argos_available:
            self._initialize_translation_pairs()
    
    def _check_argos_available(self):
        """Check if ArgosTranslate is available"""
        try:
            import argostranslate.package
            import argostranslate.translate
            self.argos_package = argostranslate.package
            self.argos_translate = argostranslate.translate
            logger.info("ArgosTranslate library available")
            return True
        except ImportError:
            logger.warning("ArgosTranslate library not available. Offline translation will be limited.")
            return False
    
    def _initialize_translation_pairs(self):
        """Initialize translation pairs for offline use"""
        if not self.argos_available:
            return
        
        # Define package URLs
        package_urls = {
            'en-tl': "https://github.com/argosopentech/argos-translate/releases/download/v1.0/en_tl.argosmodel",
            'tl-en': "https://github.com/argosopentech/argos-translate/releases/download/v1.0/tl_en.argosmodel",
            'en-ko': "https://github.com/argosopentech/argos-translate/releases/download/v1.0/en_ko.argosmodel",
            'ko-en': "https://github.com/argosopentech/argos-translate/releases/download/v1.0/ko_en.argosmodel"
        }
        
        # Define package directory
        package_dir = Path(os.path.dirname(os.path.abspath(__file__)), "argos_packages")
        os.makedirs(package_dir, exist_ok=True)
        
        # Download and install packages
        for pair, url in package_urls.items():
            try:
                # Download if not already installed
                if not self._is_translation_pair_installed(pair):
                    logger.info(f"Downloading translation package for {pair}...")
                    
                    # Download to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    urllib.request.urlretrieve(url, temp_path)
                    
                    # Install the package
                    self.argos_package.install_from_path(temp_path)
                    
                    # Remove the temporary file
                    os.unlink(temp_path)
                    
                    logger.info(f"Translation package for {pair} installed successfully")
                else:
                    logger.info(f"Translation package for {pair} already installed")
            except Exception as e:
                logger.error(f"Failed to download and install translation package for {pair}: {e}")
        
        # Update available translation pairs
        from_codes = self.argos_translate.get_available_source_languages()
        for from_lang in from_codes:
            from_code = from_lang.code
            to_codes = from_lang.get_available_target_languages()
            for to_lang in to_codes:
                to_code = to_lang.code
                pair_key = f"{from_code}-{to_code}"
                translation_function = lambda text, f=from_lang, t=to_lang: f.get_translation(t).translate(text)
                self.translation_pairs[pair_key] = translation_function
                logger.info(f"Loaded translation pair: {pair_key}")
    
    def _is_translation_pair_installed(self, pair):
        """Check if a translation pair is already installed"""
        from_code, to_code = pair.split('-')
        from_langs = self.argos_translate.get_available_source_languages()
        
        for from_lang in from_langs:
            if from_lang.code == from_code:
                to_langs = from_lang.get_available_target_languages()
                for to_lang in to_langs:
                    if to_lang.code == to_code:
                        return True
                        
        return False
    
    def _get_intermediate_translations(self, from_code, to_code):
        """
        Get a list of intermediate translations to use if direct translation is not available
        
        Args:
            from_code (str): Source language code
            to_code (str): Target language code
            
        Returns:
            list: List of language code pairs to use for translation
        """
        # If we need to translate through English
        if from_code not in ['en'] and to_code not in ['en']:
            # First translate to English, then to target language
            return [(from_code, 'en'), ('en', to_code)]
        
        # No intermediate translation needed
        return [(from_code, to_code)]
    
    def translate(self, text, from_lang='auto', to_lang='en', online=False):
        """
        Translate text from one language to another
        
        Args:
            text (str): Text to translate
            from_lang (str): Source language code ('en', 'tl', 'ko', 'auto')
            to_lang (str): Target language code ('en', 'tl', 'ko')
            online (bool): Whether to use online translation if available
            
        Returns:
            str: Translated text
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for translation")
            return ""
        
        # Handle auto-detection
        if from_lang == 'auto' or from_lang == to_lang:
            # If source is auto or same as target, try to detect the language
            try:
                from .language_detector import LanguageDetector
                detector = LanguageDetector()
                from_lang = detector.detect(text)
                logger.info(f"Auto-detected language: {from_lang}")
            except Exception as e:
                logger.error(f"Language detection failed: {e}")
                from_lang = 'en'  # Default to English
        
        # If source and target are the same after detection, return the original text
        if from_lang == to_lang:
            return text
        
        # Try online translation first if requested
        if online:
            try:
                translated = self._translate_online(text, from_lang, to_lang)
                if translated:
                    return translated
            except Exception as e:
                logger.error(f"Online translation failed: {e}")
                logger.info("Falling back to offline translation")
        
        # Offline translation with ArgosTranslate
        if self.argos_available:
            try:
                # Check if we have a direct translation path
                pair_key = f"{from_lang}-{to_lang}"
                if pair_key in self.translation_pairs:
                    logger.info(f"Using direct translation path: {pair_key}")
                    return self.translation_pairs[pair_key](text)
                
                # If no direct path, try intermediate translations
                translations = self._get_intermediate_translations(from_lang, to_lang)
                if translations:
                    logger.info(f"Using intermediate translation path: {translations}")
                    result = text
                    for src, tgt in translations:
                        pair_key = f"{src}-{tgt}"
                        if pair_key in self.translation_pairs:
                            result = self.translation_pairs[pair_key](result)
                        else:
                            logger.error(f"Translation pair not available: {pair_key}")
                            return f"[Translation not available for {src} to {tgt}]"
                    return result
            except Exception as e:
                logger.error(f"Offline translation error: {e}")
        
        # Fallback to a simple message if all translation methods fail
        logger.error(f"All translation methods failed for {from_lang} to {to_lang}")
        return f"[Translation not available for {from_lang} to {to_lang}]"
    
    def _translate_online(self, text, from_lang, to_lang):
        """
        Translate text using online translation service (Google Translate)
        
        Args:
            text (str): Text to translate
            from_lang (str): Source language code
            to_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        try:
            # Try to use googletrans library
            from googletrans import Translator as GoogleTranslator
            translator = GoogleTranslator()
            result = translator.translate(text, src=from_lang, dest=to_lang)
            return result.text
        except ImportError:
            logger.warning("googletrans library not available")
            
            # Try to use the Google Translate API directly
            try:
                import urllib.parse
                import urllib.request
                
                # Define the API URL
                url = "https://translate.googleapis.com/translate_a/single"
                
                # Define parameters
                params = {
                    'client': 'gtx',
                    'sl': from_lang,
                    'tl': to_lang,
                    'dt': 't',
                    'q': text
                }
                
                # Encode the parameters and create the request URL
                url = url + '?' + urllib.parse.urlencode(params)
                
                # Send the request
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'Mozilla/5.0')
                
                # Get the response
                response = urllib.request.urlopen(request)
                response_data = response.read().decode('utf-8')
                
                # Parse the response
                result = json.loads(response_data)
                
                # Extract the translated text
                translated_text = ''
                for sentence in result[0]:
                    if sentence[0]:
                        translated_text += sentence[0]
                
                return translated_text
                
            except Exception as e:
                logger.error(f"Direct Google Translate API request failed: {e}")
                raise
    
    def get_supported_languages(self):
        """Get the list of supported languages"""
        return self.supported_languages
        
    def detect_language(self, text):
        """
        Detect the language of a given text
        
        Args:
            text (str): Text to detect language
            
        Returns:
            str: Detected language code
        """
        if not text or not text.strip():
            return 'en'  # Default to English for empty text
            
        try:
            from .language_detector import LanguageDetector
            detector = LanguageDetector()
            return detector.detect(text)
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'en'  # Default to English on error
