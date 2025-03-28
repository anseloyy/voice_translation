/**
 * Language Detector Module
 * 
 * This module handles language detection for the translation system
 * It communicates with the backend API to detect the language of the provided text
 */

const languageDetector = (() => {
    // Private variables and methods
    let _lastDetectedLanguage = null;
    
    const _languageCodeMap = {
        'en': 'English',
        'tl': 'Filipino',
        'ko': 'Korean',
        'auto': 'Auto Detect'
    };
    
    /**
     * Convert language code to language name
     * @param {string} code - Language code
     * @returns {string} - Language name or the code if not found
     */
    const _getLanguageName = (code) => {
        return _languageCodeMap[code] || code;
    };
    
    /**
     * Detect the language of the provided text
     * @param {string} text - Text to detect language from
     * @returns {Promise<string>} - Promise resolving to language code
     */
    const detect = async (text) => {
        if (!text || text.trim() === '') {
            console.error('Empty text provided for language detection');
            return 'en'; // Default to English for empty text
        }
        
        try {
            // Call the backend API for language detection
            const response = await fetch('/api/detect-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            _lastDetectedLanguage = data.language;
            
            console.log(`Detected language: ${_getLanguageName(_lastDetectedLanguage)} (${_lastDetectedLanguage})`);
            return _lastDetectedLanguage;
            
        } catch (error) {
            console.error('Language detection error:', error);
            return 'en'; // Default to English on error
        }
    };
    
    /**
     * Get the last detected language
     * @returns {string|null} - Last detected language code or null
     */
    const getLastDetectedLanguage = () => {
        return _lastDetectedLanguage;
    };
    
    // Public API
    return {
        detect,
        getLastDetectedLanguage,
        getLanguageName: _getLanguageName
    };
})();
