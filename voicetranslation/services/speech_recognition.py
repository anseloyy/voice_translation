import logging
import os
import json
import queue
import threading
import time
from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
import numpy as np
import pyaudio
from config import Config

logger = logging.getLogger(__name__)

# Set Vosk logging level (less verbose)
SetLogLevel(0)

# Global variables
audio_queue = queue.Queue()
stop_recording = threading.Event()
is_recording = threading.Event()
current_recognizer = None
current_model = None
current_language = None
models = {}
silence_timeout = Config.SILENCE_TIMEOUT
inactivity_timeout = Config.INACTIVITY_TIMEOUT

# Audio parameters
RATE = 16000
CHANNELS = 1
CHUNK = 4096
FORMAT = pyaudio.paInt16

# Audio device
p = None

def initialize():
    """Initialize the speech recognition service"""
    global p
    logger.info("Initializing speech recognition service...")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Load models
    load_models()
    
    logger.info("Speech recognition service initialized")

def load_models():
    """Load Vosk speech recognition models"""
    global models
    
    model_dir = Config.VOSK_MODEL_DIR
    
    # Ensure model directory exists
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        logger.warning(f"Created model directory: {model_dir}. Models need to be downloaded.")
    
    # Try to load models for each language
    for lang_code, model_name in Config.VOSK_MODEL_FILES.items():
        model_path = os.path.join(model_dir, model_name)
        
        if os.path.exists(model_path):
            try:
                logger.info(f"Loading speech model for {lang_code}: {model_path}")
                models[lang_code] = Model(model_path)
                logger.info(f"Successfully loaded model for {lang_code}")
            except Exception as e:
                logger.error(f"Error loading model for {lang_code}: {e}")
        else:
            logger.warning(f"Model for {lang_code} not found at {model_path}")
    
    if not models:
        logger.warning("No speech recognition models were loaded. Speech recognition will not work.")

def create_recognizer(language):
    """Create a recognizer for the specified language"""
    global current_recognizer, current_model, current_language
    
    if language not in models:
        logger.error(f"No model available for language {language}. Falling back to English if available.")
        language = 'en' if 'en' in models else next(iter(models), None)
        
        if language is None:
            logger.error("No speech models available.")
            return None
    
    current_model = models[language]
    current_recognizer = KaldiRecognizer(current_model, RATE)
    current_language = language
    
    logger.info(f"Created recognizer for language: {language}")
    return current_recognizer

def record_audio(callback=None, language='en'):
    """
    Record audio and recognize speech
    
    Args:
        callback: Function to call with recognized text
        language: Language code for recognition
    """
    global is_recording, current_recognizer
    
    if is_recording.is_set():
        logger.warning("Already recording")
        return False
    
    # Reset stop flag
    stop_recording.clear()
    
    # Create recognizer for language if needed
    if current_language != language or current_recognizer is None:
        current_recognizer = create_recognizer(language)
        if current_recognizer is None:
            return False
    
    # Set recording flag
    is_recording.set()
    
    # Start recording thread
    threading.Thread(target=_record_audio_thread, args=(callback, language)).start()
    
    logger.info(f"Started recording for language: {language}")
    return True

def _record_audio_thread(callback, language):
    """Background thread for audio recording and recognition"""
    global is_recording, p
    
    stream = None
    
    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        logger.info("Audio stream opened")
        
        # Variables for silence detection
        last_audio_time = time.time()
        silence_start_time = None
        final_result = {"text": ""}
        
        while not stop_recording.is_set():
            if stream.is_stopped():
                stream.start_stream()
            
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Check for silence
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume_norm = np.linalg.norm(audio_data / 32768.0)
            
            # If there's audio activity
            if volume_norm > 0.01:  # Adjust this threshold as needed
                last_audio_time = time.time()
                silence_start_time = None
            else:
                # Start tracking silence
                if silence_start_time is None:
                    silence_start_time = time.time()
                
                # Check if silence timeout reached
                if silence_start_time and (time.time() - silence_start_time) > silence_timeout:
                    logger.info("Silence detected for timeout period, finalizing recognition")
                    break
                
                # Check inactivity timeout
                if (time.time() - last_audio_time) > inactivity_timeout:
                    logger.info("Inactivity timeout reached, stopping recording")
                    break
            
            # Process audio data with Vosk
            if current_recognizer.AcceptWaveform(data):
                result = json.loads(current_recognizer.Result())
                if 'text' in result and result['text'].strip():
                    final_result = result
                    if callback:
                        callback(result['text'], language, False)  # Partial result
        
        # Get final result
        result = json.loads(current_recognizer.FinalResult())
        if 'text' in result and result['text'].strip():
            final_result = result
        
        # Call callback with final result
        if callback and final_result['text'].strip():
            callback(final_result['text'], language, True)  # Final result
        
        logger.info("Recording finished")
    
    except Exception as e:
        logger.error(f"Error in recording thread: {e}")
    
    finally:
        # Clean up
        is_recording.clear()
        
        if stream:
            try:
                stream.stop_stream()
                stream.close()
                logger.info("Audio stream closed")
            except:
                pass

def stop_recording_audio():
    """Stop the audio recording"""
    global stop_recording
    
    if is_recording.is_set():
        logger.info("Stopping recording")
        stop_recording.set()
        return True
    else:
        logger.warning("Not recording")
        return False

def get_recording_status():
    """Get the current recording status"""
    return {
        "is_recording": is_recording.is_set(),
        "current_language": current_language
    }

def recognize_audio_file(file_path, language='en'):
    """
    Recognize speech from an audio file
    
    Args:
        file_path: Path to audio file
        language: Language code for recognition
        
    Returns:
        Recognized text
    """
    if language not in models:
        logger.error(f"No model available for language {language}")
        return None
    
    try:
        wf = wave.open(file_path, "rb")
        
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            logger.error("Audio file must be WAV format mono PCM")
            return None
        
        recognizer = KaldiRecognizer(models[language], wf.getframerate())
        
        results = []
        while True:
            data = wf.readframes(CHUNK)
            if len(data) == 0:
                break
            
            if recognizer.AcceptWaveform(data):
                partial_result = json.loads(recognizer.Result())
                if 'text' in partial_result and partial_result['text'].strip():
                    results.append(partial_result['text'])
        
        final_result = json.loads(recognizer.FinalResult())
        if 'text' in final_result and final_result['text'].strip():
            results.append(final_result['text'])
        
        return " ".join(results)
    
    except Exception as e:
        logger.error(f"Error recognizing audio file: {e}")
        return None
