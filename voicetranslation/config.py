import os
import logging

class Config:
    # Application settings
    DEBUG = True
    TESTING = False
    
    # Language settings
    LANGUAGES = {
        'en': 'English',
        'tl': 'Filipino',
        'ko': 'Korean'
    }
    
    DEFAULT_SOURCE_LANG = 'en'
    DEFAULT_TARGET_LANG = 'tl'
    
    # Speech recognition settings
    VOSK_MODEL_DIR = 'models/vosk'
    VOSK_MODEL_FILES = {
        'en': 'vosk-model-small-en-us',
        'tl': 'vosk-model-tl-ph',
        'ko': 'vosk-model-ko-kr'
    }
    
    # Language detection settings
    FASTTEXT_MODEL_PATH = 'models/fasttext/lid.176.bin'
    
    # Translation settings
    ARGOS_MODELS_DIR = 'models/argos'
    
    # Text-to-speech settings
    PIPER_MODEL_DIR = 'models/piper'
    PIPER_MODELS = {
        'en': {'model': 'en_US-lessac-medium', 'speaker': 'default'},
        'tl': {'model': 'es_ES-davefx-medium', 'speaker': 'default'},  # Using Spanish as substitute for Filipino
        'ko': {'model': 'vi_VN-vais1000-medium', 'speaker': 'default'}  # Using Vietnamese as substitute for Korean
    }
    
    # Hardware settings (Raspberry Pi)
    # GPIO Pin assignments
    PIN_MIC_BUTTON = 17
    PIN_PROCESS_BUTTON = 27
    PIN_MODE_BUTTON = 22
    PIN_SRC_LANG_BUTTON = 23
    PIN_TGT_LANG_BUTTON = 24
    PIN_MOTION_SENSOR = 18
    
    # Timing settings
    SILENCE_TIMEOUT = 5  # seconds
    INACTIVITY_TIMEOUT = 10  # seconds
    
    # Network settings
    NETWORK_CHECK_URL = "https://www.google.com"
    NETWORK_CHECK_INTERVAL = 60  # seconds
    
    # WebSocket settings
    PING_INTERVAL = 25  # seconds
    
    # Language mapping for translation services
    LANGUAGE_CODE_MAPPING = {
        # ISO 639-1 to Google Translate codes
        'en': 'en',
        'tl': 'tl',  # Filipino
        'ko': 'ko',
        
        # User-friendly names to codes
        'English': 'en',
        'Filipino': 'tl',
        'Korean': 'ko'
    }
    
    # System messages
    MESSAGES = {
        'en': {
            'greeting': 'Hello! Welcome to the translation system.',
            'mode_translation': 'Translation mode activated.',
            'mode_assistant': 'Assistant mode activated.',
            'mic_on': 'Microphone is on. Please speak.',
            'mic_off': 'Microphone turned off.',
            'processing': 'Processing your request.',
            'source_lang': 'Source language set to {}.',
            'target_lang': 'Target language set to {}.',
            'no_speech': 'No speech detected.',
            'error': 'An error occurred. Please try again.'
        },
        'tl': {
            'greeting': 'Kamusta! Maligayang pagdating sa sistema ng pagsasalin.',
            'mode_translation': 'Aktibo ang mode ng pagsasalin.',
            'mode_assistant': 'Aktibo ang mode ng assistant.',
            'mic_on': 'Ang mikropono ay bukas. Magsalita po kayo.',
            'mic_off': 'Ang mikropono ay nakapatay.',
            'processing': 'Pinoproseso ang iyong kahilingan.',
            'source_lang': 'Ang pinagmulang wika ay itinakda sa {}.',
            'target_lang': 'Ang target na wika ay itinakda sa {}.',
            'no_speech': 'Walang nadetektang pagsasalita.',
            'error': 'May naganap na error. Pakisubukan muli.'
        },
        'ko': {
            'greeting': '안녕하세요! 번역 시스템에 오신 것을 환영합니다.',
            'mode_translation': '번역 모드가 활성화되었습니다.',
            'mode_assistant': '어시스턴트 모드가 활성화되었습니다.',
            'mic_on': '마이크가 켜져 있습니다. 말씀해 주세요.',
            'mic_off': '마이크가 꺼졌습니다.',
            'processing': '요청을 처리하고 있습니다.',
            'source_lang': '원본 언어가 {}로 설정되었습니다.',
            'target_lang': '대상 언어가 {}로 설정되었습니다.',
            'no_speech': '음성이 감지되지 않았습니다.',
            'error': '오류가 발생했습니다. 다시 시도해 주세요.'
        }
    }
