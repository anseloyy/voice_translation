import os
import logging
import threading
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import platform

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import modules based on platform
system_platform = platform.system()
is_raspberry_pi = system_platform == 'Linux' and os.path.exists('/sys/firmware/devicetree/base/model') and 'Raspberry Pi' in open('/sys/firmware/devicetree/base/model').read()

# Initialize models
from models.language_detector import LanguageDetector
from models.speech_recognition import SpeechRecognizer
from models.translation import Translator
from models.tts import TextToSpeech
from models.ai_assistant import AIAssistant

# Import hardware modules on Raspberry Pi
if is_raspberry_pi:
    from hardware.gpio_handler import GPIOHandler
    from hardware.motion_sensor import MotionSensor
    
# Import utility modules
from utils.network import NetworkChecker
from utils.timeout import TimeoutHandler

# Import services
from services.ai_assistant import initialize as initialize_ai_assistant
from services.ai_assistant import process_query, is_available as is_ai_available

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
socketio = SocketIO(app)

# Initialize components
language_detector = LanguageDetector()
speech_recognizer = SpeechRecognizer()
translator = Translator()
tts = TextToSpeech()
network_checker = NetworkChecker()
timeout_handler = TimeoutHandler()

# Initialize AI assistant in background
threading.Thread(target=initialize_ai_assistant, daemon=True).start()

# Initialize hardware on Raspberry Pi
if is_raspberry_pi:
    gpio_handler = GPIOHandler(on_button_press_callback=lambda button_type: socketio.emit('button_press', {'button': button_type}))
    motion_sensor = MotionSensor(on_motion_detected=lambda: socketio.emit('motion_detected'))
    
    # Start hardware monitoring in separate threads
    threading.Thread(target=gpio_handler.start_monitoring, daemon=True).start()
    threading.Thread(target=motion_sensor.start_monitoring, daemon=True).start()

# Routes
@app.route('/')
def index():
    """Route to determine which interface to serve based on user agent or environment"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Check if we're on Raspberry Pi
    if is_raspberry_pi:
        return render_template('kiosk.html')
    
    # Check if mobile
    is_mobile = any(device in user_agent.lower() for device in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
    
    if is_mobile:
        return render_template('mobile.html')
    else:
        return render_template('index.html')

@app.route('/mobile')
def mobile():
    """Explicit route for mobile interface"""
    return render_template('mobile.html')

@app.route('/kiosk')
def kiosk():
    """Explicit route for kiosk interface"""
    return render_template('kiosk.html')

# API endpoints
@app.route('/api/detect-language', methods=['POST'])
def detect_language():
    """API endpoint to detect language from text"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    detected_language = language_detector.detect(text)
    return jsonify({'language': detected_language})

@app.route('/api/translate', methods=['POST'])
def translate():
    """API endpoint to translate text"""
    data = request.json
    text = data.get('text', '')
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Auto-detect language if needed
    if source_lang == 'auto':
        source_lang = language_detector.detect(text)
    
    # Translate
    online_mode = network_checker.is_online()
    translated_text = translator.translate(text, source_lang, target_lang, online=online_mode)
    
    return jsonify({
        'source_text': text,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'translated_text': translated_text,
        'online_mode': online_mode
    })

@app.route('/api/speak', methods=['POST'])
def speak():
    """API endpoint to convert text to speech"""
    data = request.json
    text = data.get('text', '')
    language = data.get('language', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Generate audio file path
    audio_data = tts.speak(text, language)
    
    return jsonify({
        'text': text,
        'language': language,
        'audio_data': audio_data
    })

@app.route('/api/assistant', methods=['POST'])
def assistant():
    """API endpoint for AI assistant queries"""
    data = request.json
    query_text = data.get('text', '')
    source_lang = data.get('source_lang', 'auto')
    response_lang = data.get('response_lang', 'en')
    
    if not query_text:
        return jsonify({'error': 'No query text provided'}), 400
    
    # Process query
    response = process_query(query_text, source_lang, response_lang)
    
    return jsonify(response)

@app.route('/api/assistant-status', methods=['GET'])
def assistant_status():
    """API endpoint to check AI assistant availability"""
    available = is_ai_available()
    return jsonify({
        'available': available,
        'model_name': 'mistral-7b-openorca-Q_4_K_M' if available else None
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection to WebSocket"""
    logger.debug('Client connected')
    
    # Send system status on connect
    is_online = network_checker.is_online()
    
    # Check AI assistant availability (handle potential exceptions)
    ai_available = False
    try:
        ai_available = is_ai_available()
    except Exception as e:
        logger.error(f"Error checking AI assistant availability: {e}")
    
    socketio.emit('system_status', {
        'online': is_online,
        'platform': 'raspberry_pi' if is_raspberry_pi else 'web',
        'supported_languages': {
            'stt': speech_recognizer.get_supported_languages(),
            'tts': tts.get_supported_languages(),
            'translation': translator.get_supported_languages()
        },
        'ai_assistant': {
            'available': ai_available,
            'model': 'mistral-7b-openorca-Q_4_K_M' if ai_available else None
        }
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection from WebSocket"""
    logger.debug('Client disconnected')

@socketio.on('start_listening')
def handle_start_listening(data):
    """Start speech recognition"""
    language = data.get('language', 'en')
    timeout_handler.reset_timeout()
    
    # Determine if online mode is available
    online_mode = network_checker.is_online()
    
    socketio.emit('listening_status', {'status': 'started'})
    
    # In a real implementation, we'd start a background thread for audio streaming
    # For this demo, we'll just acknowledge the request
    socketio.emit('system_message', {'message': f'Started listening in {language} language, online mode: {online_mode}'})

@socketio.on('stop_listening')
def handle_stop_listening():
    """Stop speech recognition"""
    socketio.emit('listening_status', {'status': 'stopped'})
    socketio.emit('system_message', {'message': 'Stopped listening'})

@socketio.on('change_mode')
def handle_change_mode(data):
    """Change between translation and assistant mode"""
    mode = data.get('mode', 'translation')
    socketio.emit('mode_changed', {'mode': mode})
    socketio.emit('system_message', {'message': f'Switched to {mode} mode'})

@socketio.on('change_language')
def handle_change_language(data):
    """Change input or output language"""
    language_type = data.get('type', 'input')  # input or output
    language = data.get('language', 'en')
    
    socketio.emit('language_changed', {
        'type': language_type,
        'language': language
    })
    
    # Announce language change
    if language == 'en':
        language_name = 'English'
    elif language == 'tl':
        language_name = 'Filipino'
    elif language == 'ko':
        language_name = 'Korean'
    else:
        language_name = language
    
    socketio.emit('system_message', {'message': f'{language_type.capitalize()} language changed to {language_name}'})

@socketio.on('assistant_query')
def handle_assistant_query(data):
    """Handle AI assistant query via WebSocket"""
    query_text = data.get('text', '')
    source_lang = data.get('source_lang', 'auto')
    response_lang = data.get('response_lang', 'en')
    
    if not query_text:
        socketio.emit('assistant_error', {'message': 'No query text provided'})
        return
    
    # Reset timeout
    timeout_handler.reset_timeout()
    
    # Notify client that we're processing
    socketio.emit('assistant_processing', {'status': 'processing'})
    
    # Process query asynchronously
    def process_callback(response):
        # Send response when ready
        socketio.emit('assistant_response', response)
    
    # Start asynchronous processing
    process_query(query_text, source_lang, response_lang, process_callback)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
