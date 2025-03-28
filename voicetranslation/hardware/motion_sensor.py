"""
Motion Sensor Module

This module handles interactions with the PIR motion sensor on Raspberry Pi
"""

import os
import logging
import threading
import time

logger = logging.getLogger(__name__)

class MotionSensor:
    """Class for handling PIR motion sensor on Raspberry Pi"""
    
    def __init__(self, on_motion_detected=None, pin=4):
        """
        Initialize the motion sensor
        
        Args:
            on_motion_detected (callable): Callback function for motion detection events
            pin (int): GPIO pin number for the PIR sensor
        """
        self.is_raspberry_pi = self._check_raspberry_pi()
        self.on_motion_detected = on_motion_detected
        self.pin = pin
        self.pir_sensor = None
        self.running = False
        self.last_motion_time = 0
        self.motion_cooldown = 10  # Seconds before triggering again
        
        if self.is_raspberry_pi:
            self._initialize_sensor()
    
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
    
    def _initialize_sensor(self):
        """Initialize the PIR motion sensor"""
        if not self.is_raspberry_pi:
            return
        
        try:
            from gpiozero import MotionSensor as PIRSensor
            
            # Initialize the PIR sensor
            self.pir_sensor = PIRSensor(self.pin)
            
            # Set up event handlers
            self.pir_sensor.when_motion = self._on_motion
            self.pir_sensor.when_no_motion = self._on_no_motion
            
            logger.info(f"PIR motion sensor initialized on GPIO pin {self.pin}")
            
        except ImportError:
            logger.error("gpiozero library not available. Motion sensor functionality will be disabled.")
            self.is_raspberry_pi = False
        except Exception as e:
            logger.error(f"Error initializing PIR motion sensor: {e}")
            self.is_raspberry_pi = False
    
    def _on_motion(self):
        """Handle motion detection event"""
        current_time = time.time()
        
        # Check if we're in the cooldown period
        if current_time - self.last_motion_time < self.motion_cooldown:
            return
        
        self.last_motion_time = current_time
        logger.info("Motion detected")
        
        if self.on_motion_detected:
            self.on_motion_detected()
    
    def _on_no_motion(self):
        """Handle no motion event"""
        logger.debug("No motion detected")
    
    def start_monitoring(self):
        """Start monitoring for motion in a separate thread"""
        if not self.is_raspberry_pi or not self.pir_sensor or self.running:
            return
        
        self.running = True
        logger.info("Started monitoring PIR motion sensor")
        
        # In a real implementation, we'd use event-based monitoring
        # Here we just keep the thread alive to prevent it from exiting
        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in motion sensor monitoring thread: {e}")
        finally:
            self.running = False
    
    def stop_monitoring(self):
        """Stop monitoring for motion"""
        self.running = False
        logger.info("Stopped monitoring PIR motion sensor")
