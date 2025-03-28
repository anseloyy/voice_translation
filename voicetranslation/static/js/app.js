/**
 * Main application script for the Multilingual Voice-to-Text Translation System
 * This script coordinates all the components and handles the UI interactions
 */

// Global state
const state = {
    mode: 'translation', // 'translation' or 'assistant'
    isListening: false,
    inputLanguage: 'auto',
    outputLanguage: 'en',
    transcript: '',
    translatedText: '',
    isOnline: false,
    isPlatformRaspberryPi: false,
    supportedLanguages: {
        stt: [],
        tts: [],
        translation: []
    },
    timeout: null
};

// Initialize socket connection
const socket = io();

// DOM elements
const elements = {
    modeTranslation: document.getElementById('translation-mode'),
    modeAssistant: document.getElementById('assistant-mode'),
    inputLanguage: document.getElementById('input-language'),
    outputLanguage: document.getElementById('output-language'),
    microphoneBtn: document.getElementById('microphone-btn'),
    speakBtn: document.getElementById('speak-btn'),
    transcript: document.getElementById('transcript'),
    translationOutput: document.getElementById('translation-output'),
    outputHeader: document.getElementById('output-header'),
    progressBar: document.getElementById('progress-bar'),
    statusIndicator: document.getElementById('status-indicator'),
    listeningStatus: document.getElementById('listening-status'),
    systemMessage: document.getElementById('system-message')
};

// Initialize language displays for kiosk mode
const inputLanguageDisplay = document.getElementById('input-language-display');
const outputLanguageDisplay = document.getElementById('output-language-display');
const currentMode = document.getElementById('current-mode');

// Helper functions
function updateSystemMessage(message, type = 'info') {
    if (elements.systemMessage) {
        elements.systemMessage.textContent = message;
        elements.systemMessage.className = `alert alert-${type}`;
    }
}

function updateConnectionStatus(isOnline) {
    state.isOnline = isOnline;
    if (elements.statusIndicator) {
        elements.statusIndicator.textContent = isOnline ? 'Online' : 'Offline';
        elements.statusIndicator.className = isOnline ? 'badge bg-success' : 'badge bg-secondary';
    }
}

function updateListeningStatus(isListening) {
    state.isListening = isListening;
    if (elements.listeningStatus) {
        elements.listeningStatus.textContent = isListening ? 'Listening...' : 'Not Listening';
        elements.listeningStatus.className = isListening ? 'badge bg-danger' : 'badge bg-secondary';
    }
    
    if (elements.microphoneBtn) {
        if (isListening) {
            elements.microphoneBtn.classList.add('active');
        } else {
            elements.microphoneBtn.classList.remove('active');
        }
    }
}

function setMode(mode) {
    state.mode = mode;
    
    if (elements.outputHeader) {
        elements.outputHeader.textContent = mode === 'translation' ? 'Translation Output' : 'Assistant Response';
    }
    
    if (currentMode) {
        currentMode.textContent = mode === 'translation' ? 'Translation Mode' : 'Assistant Mode';
    }
    
    // Clear outputs when switching modes
    if (elements.translationOutput) {
        elements.translationOutput.innerHTML = `<p class="text-muted">${mode === 'translation' ? 'Translation' : 'Assistant response'} will appear here...</p>`;
    }
    
    updateSystemMessage(`Switched to ${mode} mode`);
    
    // Send mode change to server
    socket.emit('change_mode', { mode });
}

function setInputLanguage(language) {
    state.inputLanguage = language;
    
    if (elements.inputLanguage) {
        elements.inputLanguage.value = language;
    }
    
    if (inputLanguageDisplay) {
        const languageNames = {
            'auto': 'Auto Detect',
            'en': 'English',
            'tl': 'Filipino',
            'ko': 'Korean'
        };
        inputLanguageDisplay.textContent = languageNames[language] || language;
    }
    
    socket.emit('change_language', { type: 'input', language });
    
    // Speak the language selection
    if (state.isPlatformRaspberryPi) {
        const languageText = {
            'auto': 'Auto Detect Language',
            'en': 'Input language: English',
            'tl': 'Input language: Filipino',
            'ko': 'Input language: Korean'
        };
        
        // Use TTS to announce the language change
        tts.speak(languageText[language] || `Input language: ${language}`, 'en');
    }
}

function setOutputLanguage(language) {
    state.outputLanguage = language;
    
    if (elements.outputLanguage) {
        elements.outputLanguage.value = language;
    }
    
    if (outputLanguageDisplay) {
        const languageNames = {
            'en': 'English',
            'tl': 'Filipino',
            'ko': 'Korean'
        };
        outputLanguageDisplay.textContent = languageNames[language] || language;
    }
    
    socket.emit('change_language', { type: 'output', language });
    
    // Speak the language selection
    if (state.isPlatformRaspberryPi) {
        const languageText = {
            'en': 'Output language: English',
            'tl': 'Output language: Filipino',
            'ko': 'Output language: Korean'
        };
        
        // Use TTS to announce the language change
        tts.speak(languageText[language] || `Output language: ${language}`, 'en');
    }
}

function cycleInputLanguage() {
    const languages = ['auto', 'en', 'tl', 'ko'];
    const currentIndex = languages.indexOf(state.inputLanguage);
    const nextIndex = (currentIndex + 1) % languages.length;
    setInputLanguage(languages[nextIndex]);
}

function cycleOutputLanguage() {
    const languages = ['en', 'tl', 'ko'];
    const currentIndex = languages.indexOf(state.outputLanguage);
    const nextIndex = (currentIndex + 1) % languages.length;
    setOutputLanguage(languages[nextIndex]);
}

function startListening() {
    if (state.isListening) return;
    
    updateListeningStatus(true);
    updateSystemMessage('Listening... Speak now');
    
    // Reset progress bar
    if (elements.progressBar) {
        elements.progressBar.style.width = '0%';
        elements.progressBar.classList.remove('progress-active');
        void elements.progressBar.offsetWidth; // Force reflow
        elements.progressBar.classList.add('progress-active');
    }
    
    // Clear previous transcript
    if (elements.transcript) {
        elements.transcript.value = '';
    }
    
    // Start the voice recognition
    voiceRecognition.start(state.inputLanguage, state.isOnline);
    
    // Tell the server we're listening
    socket.emit('start_listening', { language: state.inputLanguage });
    
    // Set timeout to automatically stop listening after silence
    clearTimeout(state.timeout);
    state.timeout = setTimeout(() => {
        stopListening();
        processInput();
    }, 5000); // Stop after 5 seconds of silence
}

function stopListening() {
    if (!state.isListening) return;
    
    updateListeningStatus(false);
    updateSystemMessage('Stopped listening');
    
    // Stop the voice recognition
    voiceRecognition.stop();
    
    // Reset progress bar
    if (elements.progressBar) {
        elements.progressBar.classList.remove('progress-active');
        elements.progressBar.style.width = '100%';
    }
    
    // Tell the server we stopped listening
    socket.emit('stop_listening');
    
    // Clear timeout
    clearTimeout(state.timeout);
}

function processInput() {
    const text = elements.transcript ? elements.transcript.value : '';
    
    if (!text.trim()) {
        updateSystemMessage('No speech detected. Try again.', 'warning');
        return;
    }
    
    updateSystemMessage('Processing...');
    
    if (state.mode === 'translation') {
        // For translation mode, detect language and translate
        languageDetector.detect(text)
            .then(detectedLanguage => {
                // Update input language if it was set to auto
                if (state.inputLanguage === 'auto') {
                    setInputLanguage(detectedLanguage);
                }
                
                // Translate the text
                return translator.translate(text, detectedLanguage, state.outputLanguage, state.isOnline);
            })
            .then(translatedText => {
                // Display translation
                if (elements.translationOutput) {
                    elements.translationOutput.innerHTML = `<p>${translatedText}</p>`;
                }
                
                state.translatedText = translatedText;
                
                // Automatically speak the translation if on Raspberry Pi
                if (state.isPlatformRaspberryPi) {
                    tts.speak(translatedText, state.outputLanguage);
                }
                
                updateSystemMessage('Translation complete');
            })
            .catch(error => {
                console.error('Translation error:', error);
                updateSystemMessage('Translation failed: ' + error.message, 'danger');
            });
    } else {
        // For assistant mode, this would handle AI processing
        // Currently just a placeholder
        if (elements.translationOutput) {
            elements.translationOutput.innerHTML = '<p class="text-muted">Assistant mode is ready but AI is not yet implemented.</p>';
        }
        
        updateSystemMessage('Assistant mode is ready but AI is not yet implemented.', 'info');
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI based on state
    if (elements.modeTranslation && elements.modeAssistant) {
        elements.modeTranslation.checked = state.mode === 'translation';
        elements.modeAssistant.checked = state.mode === 'assistant';
        
        elements.modeTranslation.addEventListener('change', () => {
            if (elements.modeTranslation.checked) setMode('translation');
        });
        
        elements.modeAssistant.addEventListener('change', () => {
            if (elements.modeAssistant.checked) setMode('assistant');
        });
    }
    
    if (elements.inputLanguage) {
        elements.inputLanguage.value = state.inputLanguage;
        elements.inputLanguage.addEventListener('change', (e) => {
            setInputLanguage(e.target.value);
        });
    }
    
    if (elements.outputLanguage) {
        elements.outputLanguage.value = state.outputLanguage;
        elements.outputLanguage.addEventListener('change', (e) => {
            setOutputLanguage(e.target.value);
        });
    }
    
    if (elements.microphoneBtn) {
        elements.microphoneBtn.addEventListener('click', () => {
            if (state.isListening) {
                stopListening();
                processInput();
            } else {
                startListening();
            }
        });
    }
    
    if (elements.speakBtn) {
        elements.speakBtn.addEventListener('click', () => {
            const textToSpeak = state.translatedText || (elements.translationOutput ? elements.translationOutput.textContent : '');
            if (textToSpeak && textToSpeak !== 'Translation will appear here...') {
                tts.speak(textToSpeak, state.outputLanguage);
                updateSystemMessage('Speaking translation...');
            } else {
                updateSystemMessage('No translation to speak', 'warning');
            }
        });
    }
    
    // Handle speech recognition results
    voiceRecognition.onResult = (result) => {
        if (elements.transcript) {
            elements.transcript.value = result;
            state.transcript = result;
        }
        
        // Reset silence timeout when new speech is detected
        clearTimeout(state.timeout);
        state.timeout = setTimeout(() => {
            stopListening();
            processInput();
        }, 5000); // Stop after 5 seconds of silence
    };
    
    voiceRecognition.onError = (error) => {
        updateSystemMessage(`Speech recognition error: ${error}`, 'danger');
        stopListening();
    };
    
    // Handle key presses for testing without physical buttons
    document.addEventListener('keydown', (e) => {
        // Space = Microphone
        if (e.code === 'Space') {
            e.preventDefault();
            if (state.isListening) {
                stopListening();
                processInput();
            } else {
                startListening();
            }
        }
        
        // 1 = Input Language
        else if (e.key === '1') {
            cycleInputLanguage();
        }
        
        // 2 = Output Language 
        else if (e.key === '2') {
            cycleOutputLanguage();
        }
        
        // 3 = Mode
        else if (e.key === '3') {
            setMode(state.mode === 'translation' ? 'assistant' : 'translation');
        }
        
        // S = Speak
        else if (e.key === 's' || e.key === 'S') {
            const textToSpeak = state.translatedText || (elements.translationOutput ? elements.translationOutput.textContent : '');
            if (textToSpeak && textToSpeak !== 'Translation will appear here...') {
                tts.speak(textToSpeak, state.outputLanguage);
            }
        }
    });
});

// Socket.io event handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateConnectionStatus(false);
});

socket.on('system_status', (data) => {
    updateConnectionStatus(data.online);
    state.isPlatformRaspberryPi = data.platform === 'raspberry_pi';
    state.supportedLanguages = data.supported_languages;
    
    console.log('System status:', data);
    
    // Initialize language displays for kiosk mode
    if (inputLanguageDisplay) setInputLanguage(state.inputLanguage);
    if (outputLanguageDisplay) setOutputLanguage(state.outputLanguage);
});

socket.on('system_message', (data) => {
    updateSystemMessage(data.message);
});

socket.on('listening_status', (data) => {
    updateListeningStatus(data.status === 'started');
});

socket.on('button_press', (data) => {
    console.log('Button pressed:', data.button);
    
    switch (data.button) {
        case 'microphone':
            if (state.isListening) {
                stopListening();
                processInput();
            } else {
                startListening();
            }
            break;
        
        case 'input_language':
            cycleInputLanguage();
            break;
        
        case 'output_language':
            cycleOutputLanguage();
            break;
        
        case 'mode':
            setMode(state.mode === 'translation' ? 'assistant' : 'translation');
            break;
        
        case 'process':
            if (state.isListening) {
                stopListening();
            }
            processInput();
            break;
    }
});

socket.on('motion_detected', () => {
    console.log('Motion detected');
    
    // Greet the user
    tts.speak('Welcome to the Multilingual Translation System. Press the orange button to start speaking.', 'en');
});

// Initialize the system
updateSystemMessage('System initializing...');
