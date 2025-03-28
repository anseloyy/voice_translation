"""
GPIO Handler Module

This module handles interactions with Raspberry Pi GPIO pins for physical buttons
"""

import os
import logging
import threading
import time

logger = logging.getLogger(__name__)

class GPIOHandler:
    """Class for handling GPIO pins on Raspberry Pi"""
    
    def __init__(self, on_button_press_callback=None):
        """
        Initialize the GPIO handler
        
        Args:
            on_button_press_callback (callable): Callback function for button press events
        """
        self.is_raspberry_pi = self._check_raspberry_pi()
        self.on_button_press = on_button_press_callback
        self.buttons = {}
        self.running = False
        
        if self.is_raspberry_pi:
            self._initialize_gpio()
    
    def _check_raspberry_pi(self):
        """Check if running on a Raspberry Pi"""
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    logger.info("Running on Raspberry Pi")
                    return True
        except:
            pass
        
        logger.info("Not running on Raspberry Pi")
        return False
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for buttons"""
        if not self.is_raspberry_pi:
            return
        
        try:
            from gpiozero import Button
            
            # Define button pins
            button_pins = {
                'microphone': 17,  # Orange button - GPIO17
                'input_language': 22,  # Blue button - GPIO22
                'output_language': 23,  # Green button - GPIO23
                'mode': 24,  # Red button - GPIO24
                'process': 27  # Yellow button - GPIO27
            }
            
            # Initialize buttons
            for button_name, pin in button_pins.items():
                try:
                    # Create button with pull-up resistor
                    button = Button(pin, pull_up=True, bounce_time=0.1)
                    button.when_pressed = lambda b=button_name: self._on_button_pressed(b)
                    self.buttons[button_name] = button
                    logger.info(f"Initialized button '{button_name}' on GPIO pin {pin}")
                except Exception as e:
                    logger.error(f"Failed to initialize button '{button_name}' on GPIO pin {pin}: {e}")
            
            logger.info("GPIO buttons initialized successfully")
            
        except ImportError:
            logger.error("gpiozero library not available. Button functionality will be disabled.")
            self.is_raspberry_pi = False
        except Exception as e:
            logger.error(f"Error initializing GPIO: {e}")
            self.is_raspberry_pi = False
    
    def _on_button_pressed(self, button_name):
        """
        Handle button press events
        
        Args:
            button_name (str): Name of the button that was pressed
        """
        logger.info(f"Button pressed: {button_name}")
        
        if self.on_button_press:
            self.on_button_press(button_name)
    
    def start_monitoring(self):
        """Start monitoring button presses in a separate thread"""
        if not self.is_raspberry_pi or self.running:
            return
        
        self.running = True
        logger.info("Started monitoring GPIO buttons")
        
        # In a real implementation, we'd use event-based monitoring
        # Here we just keep the thread alive to prevent it from exiting
        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in GPIO monitoring thread: {e}")
        finally:
            self.running = False
    
    def stop_monitoring(self):
        """Stop monitoring button presses"""
        self.running = False
        logger.info("Stopped monitoring GPIO buttons")
