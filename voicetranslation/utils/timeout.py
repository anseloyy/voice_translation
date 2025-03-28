"""
Timeout Utilities Module

This module provides timeout-related utilities for inactivity detection
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

class TimeoutHandler:
    """Class for handling timeouts and inactivity detection"""
    
    def __init__(self, silence_timeout=5, inactivity_timeout=10):
        """
        Initialize the timeout handler
        
        Args:
            silence_timeout (int): Timeout in seconds for silence detection
            inactivity_timeout (int): Timeout in seconds for inactivity detection
        """
        self.silence_timeout = silence_timeout
        self.inactivity_timeout = inactivity_timeout
        self.silence_timer = None
        self.inactivity_timer = None
        self.on_silence_callback = None
        self.on_inactivity_callback = None
    
    def set_silence_callback(self, callback):
        """
        Set callback function for silence timeout
        
        Args:
            callback (callable): Function to call when silence is detected
        """
        self.on_silence_callback = callback
    
    def set_inactivity_callback(self, callback):
        """
        Set callback function for inactivity timeout
        
        Args:
            callback (callable): Function to call when inactivity is detected
        """
        self.on_inactivity_callback = callback
    
    def reset_timeout(self):
        """Reset both silence and inactivity timers"""
        self.reset_silence_timer()
        self.reset_inactivity_timer()
    
    def reset_silence_timer(self):
        """Reset the silence timer"""
        if self.silence_timer:
            self.silence_timer.cancel()
        
        self.silence_timer = threading.Timer(
            self.silence_timeout,
            self._silence_timeout
        )
        self.silence_timer.daemon = True
        self.silence_timer.start()
        logger.debug(f"Silence timer reset ({self.silence_timeout}s)")
    
    def reset_inactivity_timer(self):
        """Reset the inactivity timer"""
        if self.inactivity_timer:
            self.inactivity_timer.cancel()
        
        self.inactivity_timer = threading.Timer(
            self.inactivity_timeout,
            self._inactivity_timeout
        )
        self.inactivity_timer.daemon = True
        self.inactivity_timer.start()
        logger.debug(f"Inactivity timer reset ({self.inactivity_timeout}s)")
    
    def _silence_timeout(self):
        """Handle silence timeout event"""
        logger.info(f"Silence detected (no audio for {self.silence_timeout}s)")
        
        if self.on_silence_callback:
            self.on_silence_callback()
    
    def _inactivity_timeout(self):
        """Handle inactivity timeout event"""
        logger.info(f"Inactivity detected (no interaction for {self.inactivity_timeout}s)")
        
        if self.on_inactivity_callback:
            self.on_inactivity_callback()
    
    def stop(self):
        """Stop all timers"""
        if self.silence_timer:
            self.silence_timer.cancel()
            self.silence_timer = None
        
        if self.inactivity_timer:
            self.inactivity_timer.cancel()
            self.inactivity_timer = None
        
        logger.debug("All timers stopped")
