/**
 * Voice Recognition Module
 * 
 * This module handles speech-to-text functionality
 * It uses WebSockets to stream audio to the server for processing
 */

const voiceRecognition = (() => {
    // Private variables
    let _socket = io();
    let _isListening = false;
    let _stream = null;
    let _audioContext = null;
    let _processor = null;
    let _language = 'auto';
    let _onlineMode = false;
    
    // Callback functions
    let _onResultCallback = null;
    let _onErrorCallback = null;
    
    /**
     * Start the voice recognition process
     * @param {string} language - Language code to recognize
     * @param {boolean} online - Whether to use online recognition if available
     */
    const start = async (language = 'auto', online = false) => {
        if (_isListening) return;
        
        _language = language;
        _onlineMode = online;
        
        try {
            // Request microphone access
            _stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Initialize audio processing
            _audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = _audioContext.createMediaStreamSource(_stream);
            
            // Create script processor for audio processing
            _processor = _audioContext.createScriptProcessor(4096, 1, 1);
            
            // Connect the audio graph
            source.connect(_processor);
            _processor.connect(_audioContext.destination);
            
            // Process audio data
            _processor.onaudioprocess = (e) => {
                if (!_isListening) return;
                
                // Get audio data
                const inputData = e.inputBuffer.getChannelData(0);
                
                // Convert to format suitable for transmission (16-bit PCM)
                const pcmData = convertFloatTo16BitPCM(inputData);
                
                // Send to server via WebSocket
                _socket.emit('audio_data', {
                    audio: pcmData,
                    language: _language,
                    online: _onlineMode
                });
            };
            
            _isListening = true;
            console.log(`Started voice recognition in ${_language} language, online mode: ${_onlineMode}`);
            
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            if (_onErrorCallback) {
                _onErrorCallback(error.message);
            }
        }
    };
    
    /**
     * Stop the voice recognition process
     */
    const stop = () => {
        if (!_isListening) return;
        
        // Stop the microphone stream
        if (_stream) {
            _stream.getTracks().forEach(track => track.stop());
            _stream = null;
        }
        
        // Clean up audio processing
        if (_processor && _audioContext) {
            _processor.disconnect();
            _audioContext.close();
            _processor = null;
            _audioContext = null;
        }
        
        _isListening = false;
        console.log('Stopped voice recognition');
        
        // Notify server
        _socket.emit('stop_audio');
    };
    
    /**
     * Set callback for recognition results
     * @param {Function} callback - Function to call with recognition results
     */
    const setOnResult = (callback) => {
        _onResultCallback = callback;
    };
    
    /**
     * Set callback for recognition errors
     * @param {Function} callback - Function to call with recognition errors
     */
    const setOnError = (callback) => {
        _onErrorCallback = callback;
    };
    
    /**
     * Convert Float32Array to Int16Array for efficient transmission
     * @param {Float32Array} input - Raw audio data
     * @returns {Int16Array} - Converted audio data
     */
    const convertFloatTo16BitPCM = (input) => {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            // Convert to 16-bit signed integer
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output;
    };
    
    // Set up socket event handlers
    _socket.on('recognition_result', (data) => {
        console.log('Recognition result:', data.text);
        if (_onResultCallback) {
            _onResultCallback(data.text);
        }
    });
    
    _socket.on('recognition_error', (data) => {
        console.error('Recognition error:', data.error);
        if (_onErrorCallback) {
            _onErrorCallback(data.error);
        }
    });
    
    // Public API
    return {
        start,
        stop,
        isListening: () => _isListening,
        
        // Getter/setter for callbacks
        get onResult() {
            return _onResultCallback;
        },
        set onResult(callback) {
            _onResultCallback = callback;
        },
        get onError() {
            return _onErrorCallback;
        },
        set onError(callback) {
            _onErrorCallback = callback;
        }
    };
})();
