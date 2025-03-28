/**
 * Translator Module
 * 
 * This module handles text translation between different languages
 * It communicates with the backend API for translation services
 */

const translator = (() => {
    // Private variables and methods
    let _lastTranslation = {
        sourceText: '',
        translatedText: '',
        sourceLang: '',
        targetLang: ''
    };
    
    /**
     * Translate text from source language to target language
     * @param {string} text - Text to translate
     * @param {string} sourceLang - Source language code (or 'auto' for auto-detection)
     * @param {string} targetLang - Target language code
     * @param {boolean} online - Whether to use online translation if available
     * @returns {Promise<string>} - Promise resolving to translated text
     */
    const translate = async (text, sourceLang = 'auto', targetLang = 'en', online = false) => {
        if (!text || text.trim() === '') {
            console.error('Empty text provided for translation');
            return '';
        }
        
        try {
            // Call the backend API for translation
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text,
                    source_lang: sourceLang,
                    target_lang: targetLang,
                    online: online
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update last translation data
            _lastTranslation = {
                sourceText: text,
                translatedText: data.translated_text,
                sourceLang: data.source_lang,
                targetLang: data.target_lang
            };
            
            console.log(`Translation completed: ${data.source_lang} -> ${data.target_lang} (${data.online_mode ? 'online' : 'offline'})`);
            
            return data.translated_text;
            
        } catch (error) {
            console.error('Translation error:', error);
            return `[Translation failed: ${error.message}]`;
        }
    };
    
    /**
     * Get details of the last translation
     * @returns {Object} - Last translation details
     */
    const getLastTranslation = () => {
        return { ..._lastTranslation };
    };
    
    /**
     * Check if the language pair is supported
     * @param {string} sourceLang - Source language code
     * @param {string} targetLang - Target language code
     * @returns {boolean} - Whether the language pair is supported
     */
    const isLanguagePairSupported = (sourceLang, targetLang) => {
        // All combinations of en, tl, ko should be supported
        const supportedLanguages = ['en', 'tl', 'ko'];
        return supportedLanguages.includes(sourceLang) && supportedLanguages.includes(targetLang);
    };
    
    // Public API
    return {
        translate,
        getLastTranslation,
        isLanguagePairSupported
    };
})();
