/**
 * AI Assistant Module
 * 
 * This module handles interactions with the AI assistant
 * It communicates with the backend API for AI processing
 */
(function(window) {
    'use strict';

    const AssistantModule = (function() {
        // Private variables
        let _socket = null;
        let _onResponse = null;
        let _onProcessing = null;
        let _onError = null;
        let _isAvailable = false;
        let _modelName = '';
        let _isProcessing = false;

        /**
         * Check if the AI assistant is available
         * @returns {Promise<boolean>} - Promise resolving to availability status
         */
        async function checkAvailability() {
            try {
                const response = await fetch('/api/assistant-status');
                const data = await response.json();
                _isAvailable = data.available;
                _modelName = data.model_name;
                return _isAvailable;
            } catch (error) {
                console.error('Error checking AI assistant availability:', error);
                _isAvailable = false;
                return false;
            }
        }

        /**
         * Initialize the assistant module
         * @param {object} socket - Socket.io instance
         */
        function init(socket) {
            _socket = socket;

            // Listen for assistant responses
            _socket.on('assistant_response', (data) => {
                _isProcessing = false;
                if (_onResponse) {
                    _onResponse(data);
                }
            });

            // Listen for processing status
            _socket.on('assistant_processing', (data) => {
                _isProcessing = data.status === 'processing';
                if (_onProcessing) {
                    _onProcessing(_isProcessing);
                }
            });

            // Listen for errors
            _socket.on('assistant_error', (data) => {
                _isProcessing = false;
                if (_onError) {
                    _onError(data.message);
                }
            });

            // Check availability
            checkAvailability();
        }

        /**
         * Submit a query to the AI assistant via WebSocket
         * @param {string} text - Query text
         * @param {string} sourceLang - Source language code
         * @param {string} responseLang - Response language code
         * @returns {boolean} - Whether the query was submitted successfully
         */
        function query(text, sourceLang = 'auto', responseLang = 'en') {
            if (!_socket) {
                console.error('Socket not initialized');
                return false;
            }

            if (!text) {
                if (_onError) {
                    _onError('Query text cannot be empty');
                }
                return false;
            }

            if (_isProcessing) {
                if (_onError) {
                    _onError('Already processing a query');
                }
                return false;
            }

            _isProcessing = true;
            if (_onProcessing) {
                _onProcessing(true);
            }

            _socket.emit('assistant_query', {
                text: text,
                source_lang: sourceLang,
                response_lang: responseLang
            });

            return true;
        }

        /**
         * Submit a query to the AI assistant via HTTP API
         * @param {string} text - Query text
         * @param {string} sourceLang - Source language code
         * @param {string} responseLang - Response language code
         * @returns {Promise<object>} - Promise resolving to response data
         */
        async function queryHttp(text, sourceLang = 'auto', responseLang = 'en') {
            if (!text) {
                throw new Error('Query text cannot be empty');
            }

            if (_isProcessing) {
                throw new Error('Already processing a query');
            }

            _isProcessing = true;
            if (_onProcessing) {
                _onProcessing(true);
            }

            try {
                const response = await fetch('/api/assistant', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        source_lang: sourceLang,
                        response_lang: responseLang
                    })
                });

                const data = await response.json();
                _isProcessing = false;
                
                if (_onProcessing) {
                    _onProcessing(false);
                }
                
                if (_onResponse) {
                    _onResponse(data);
                }
                
                return data;
            } catch (error) {
                _isProcessing = false;
                
                if (_onProcessing) {
                    _onProcessing(false);
                }
                
                if (_onError) {
                    _onError(error.message);
                }
                
                throw error;
            }
        }

        // Public API
        return {
            init: init,
            query: query,
            queryHttp: queryHttp,
            checkAvailability: checkAvailability,
            
            // Getters
            get isAvailable() {
                return _isAvailable;
            },
            
            get modelName() {
                return _modelName;
            },
            
            get isProcessing() {
                return _isProcessing;
            },
            
            // Event handlers
            set onResponse(callback) {
                _onResponse = callback;
            },
            
            get onResponse() {
                return _onResponse;
            },
            
            set onProcessing(callback) {
                _onProcessing = callback;
            },
            
            get onProcessing() {
                return _onProcessing;
            },
            
            set onError(callback) {
                _onError = callback;
            },
            
            get onError() {
                return _onError;
            }
        };
    })();

    // Expose the module
    window.AssistantModule = AssistantModule;
})(window);