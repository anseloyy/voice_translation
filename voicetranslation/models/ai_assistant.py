"""
AI Assistant Module

This module provides AI assistant functionality using local LLM models
"""
import os
import logging
import threading
import time
import queue
import json
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class AIAssistant:
    """Class for AI assistant using local LLM models"""
    
    def __init__(self):
        """Initialize the AI assistant"""
        self.model = None
        self.model_loaded = False
        self.response_queue = queue.Queue()
        self.is_processing = False
        self.model_dir = 'models/llm'
        self.model_name = 'mistral-7b-openorca-Q_4_K_M'
        self._load_model_thread = None
        
        # Try to load the model in a separate thread to avoid blocking startup
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize and load the LLM model in a background thread"""
        def load_model_thread():
            try:
                logger.info(f"Loading LLM model: {self.model_name}")
                self._check_llama_cpp_available()
                
                # Create model directory if it doesn't exist
                os.makedirs(self.model_dir, exist_ok=True)
                
                # Check if model file exists
                model_path = os.path.join(self.model_dir, f"{self.model_name}.gguf")
                if not os.path.exists(model_path):
                    logger.warning(f"Model file not found at {model_path}. The AI assistant will not be available.")
                    return
                
                # Import llama_cpp here to avoid blocking startup if not available
                from llama_cpp import Llama
                
                # Load the model
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=2048,        # Context window size
                    n_threads=4,       # Adjust based on Raspberry Pi capability
                    n_batch=512,       # Batch size for prompt processing
                    verbose=False      # Set to True for debugging
                )
                
                self.model_loaded = True
                logger.info(f"LLM model loaded successfully: {self.model_name}")
                
            except Exception as e:
                logger.error(f"Error loading LLM model: {str(e)}")
                self.model_loaded = False
        
        self._load_model_thread = threading.Thread(target=load_model_thread)
        self._load_model_thread.daemon = True
        self._load_model_thread.start()
    
    def _check_llama_cpp_available(self):
        """Check if llama-cpp-python is available"""
        try:
            import llama_cpp
            return True
        except ImportError:
            logger.warning("llama-cpp-python library not available. AI assistant functionality will be disabled.")
            return False
    
    def generate_response(self, input_text, language='en', async_callback=None):
        """
        Generate a response using the AI model
        
        Args:
            input_text (str): User input text
            language (str): Language code for response
            async_callback (callable): Function to call with the generated response
            
        Returns:
            str: Generated response if async_callback is None, otherwise None
        """
        if not self.model_loaded:
            response = self._get_fallback_response(language)
            if async_callback:
                async_callback(response)
                return None
            return response
            
        # If callback provided, process asynchronously
        if async_callback:
            thread = threading.Thread(
                target=self._generate_response_thread,
                args=(input_text, language, async_callback)
            )
            thread.daemon = True
            thread.start()
            return None
        
        # Otherwise, process synchronously
        return self._generate_response_sync(input_text, language)
    
    def _generate_response_thread(self, input_text, language, callback):
        """Thread function for asynchronous response generation"""
        self.is_processing = True
        response = self._generate_response_sync(input_text, language)
        self.is_processing = False
        callback(response)
    
    def _generate_response_sync(self, input_text, language):
        """Generate response synchronously"""
        try:
            # Set system prompt based on language
            system_prompts = {
                'en': "You are a helpful assistant. Provide concise and accurate information.",
                'tl': "Ikaw ay isang kapaki-pakinabang na assistant. Magbigay ng malinaw at tumpak na impormasyon.",
                'ko': "당신은 유용한 어시스턴트입니다. 간결하고 정확한 정보를 제공하세요."
            }
            
            system_prompt = system_prompts.get(language, system_prompts['en'])
            
            # Prepare prompt
            prompt = f"<s>[INST] {system_prompt}\n\nUser: {input_text} [/INST]</s>"
            
            # Generate response
            response = self.model(
                prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.95,
                stop=["</s>", "[INST]"],
                echo=False
            )
            
            # Extract text from response
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(language)
    
    def _get_fallback_response(self, language):
        """Get fallback response when model is not available"""
        fallback_responses = {
            'en': "I'm sorry, I'm having trouble processing that right now. Please try again later.",
            'tl': "Paumanhin, nahihirapan akong i-proseso iyan ngayon. Pakisubukan muli mamaya.",
            'ko': "죄송합니다, 지금 처리하는 데 어려움이 있습니다. 나중에 다시 시도해 주세요."
        }
        return fallback_responses.get(language, fallback_responses['en'])
    
    def is_available(self):
        """Check if the AI assistant is available"""
        return self.model_loaded