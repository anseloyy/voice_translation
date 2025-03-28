/**
 * Text-to-Speech Module
 * 
 * This module handles text-to-speech functionality
 * It communicates with the backend API for speech synthesis
 */

const tts = (() => {
    // Private variables
    let _audio = new Audio();
    let _isSpeaking = false;
    let _queue = [];
    let _onStartCallback = null;
    let _onEndCallback = null;
    
    /**
     * Convert text to speech and play it
     * @param {string} text - Text to convert to speech
     * @param {string} language - Language code for the voice
     * @returns {Promise<void>} - Promise that resolves when speech is complete
     */
    const speak = async (text, language = 'en') => {
        if (!text || text.trim() === '') {
            console.error('Empty text provided for speech synthesis');
            return;
        }
        
        // Add to queue if already speaking
        if (_isSpeaking) {
            _queue.push({ text, language });
            console.log('Speech added to queue');
            return;
        }
        
        try {
            _isSpeaking = true;
            
            if (_onStartCallback) {
                _onStartCallback(text, language);
            }
            
            // Call the backend API for text-to-speech
            const response = await fetch('/api/speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text,
                    language
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Play the audio
            _audio.src = 'data:audio/wav;base64,' + data.audio_data;
            
            // Set up event handlers
            _audio.onended = () => {
                _isSpeaking = false;
                
                if (_onEndCallback) {
                    _onEndCallback();
                }
                
                // Process queue
                if (_queue.length > 0) {
                    const next = _queue.shift();
                    speak(next.text, next.language);
                }
            };
            
            _audio.onerror = (error) => {
                console.error('Audio playback error:', error);
                _isSpeaking = false;
                
                if (_onEndCallback) {
                    _onEndCallback(error);
                }
                
                // Continue with queue despite error
                if (_queue.length > 0) {
                    const next = _queue.shift();
                    speak(next.text, next.language);
                }
            };
            
            // Start playback
            await _audio.play();
            console.log(`Playing speech in ${language}: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
            
        } catch (error) {
            console.error('Text-to-speech error:', error);
            _isSpeaking = false;
            
            if (_onEndCallback) {
                _onEndCallback(error);
            }
            
            // Continue with queue despite error
            if (_queue.length > 0) {
                const next = _queue.shift();
                speak(next.text, next.language);
            }
        }
    };
    
    /**
     * Stop current speech playback
     */
    const stop = () => {
        _audio.pause();
        _audio.currentTime = 0;
        _isSpeaking = false;
        _queue = []; // Clear queue
        
        console.log('Speech stopped');
        
        if (_onEndCallback) {
            _onEndCallback({ stopped: true });
        }
    };
    
    /**
     * Set callback for speech start event
     * @param {Function} callback - Function to call when speech starts
     */
    const setOnStart = (callback) => {
        _onStartCallback = callback;
    };
    
    /**
     * Set callback for speech end event
     * @param {Function} callback - Function to call when speech ends
     */
    const setOnEnd = (callback) => {
        _onEndCallback = callback;
    };
    
    /**
     * Check if currently speaking
     * @returns {boolean} - Whether currently speaking
     */
    const isSpeaking = () => {
        return _isSpeaking;
    };
    
    /**
     * Get queue length
     * @returns {number} - Number of pending speech items
     */
    const getQueueLength = () => {
        return _queue.length;
    };
    
    // Public API
    return {
        speak,
        stop,
        isSpeaking,
        getQueueLength,
        
        // Getter/setter for callbacks
        get onStart() {
            return _onStartCallback;
        },
        set onStart(callback) {
            _onStartCallback = callback;
        },
        get onEnd() {
            return _onEndCallback;
        },
        set onEnd(callback) {
            _onEndCallback = callback;
        }
    };
})();
