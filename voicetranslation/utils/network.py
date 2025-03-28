"""
Network Utilities Module

This module provides network-related utilities, including checking online status
"""

import logging
import socket
import time
import threading

logger = logging.getLogger(__name__)

class NetworkChecker:
    """Class for checking network connectivity"""
    
    def __init__(self, check_interval=30):
        """
        Initialize the network checker
        
        Args:
            check_interval (int): Interval in seconds between connectivity checks
        """
        self._online_status = False
        self.check_interval = check_interval
        self.running = False
        
        # Start background connectivity checks
        self.start_monitoring()
    
    def check_connection(self):
        """
        Check if the device is connected to the internet
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Try to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            pass
        
        try:
            # Alternative check
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True
        except OSError:
            pass
        
        return False
    
    def start_monitoring(self):
        """Start monitoring network connectivity in a background thread"""
        if self.running:
            return
        
        self.running = True
        
        def monitor_thread():
            while self.running:
                try:
                    online = self.check_connection()
                    
                    if online != self._online_status:
                        self._online_status = online
                        logger.info(f"Network status changed: {'Online' if online else 'Offline'}")
                    
                    # Sleep for the check interval
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in network monitoring: {e}")
                    time.sleep(self.check_interval)
        
        # Start monitoring in a background thread
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info(f"Started network monitoring (interval: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop monitoring network connectivity"""
        self.running = False
        logger.info("Stopped network monitoring")
    
    def is_online(self):
        """
        Get the current online status
        
        Returns:
            bool: True if online, False otherwise
        """
        return self._online_status
