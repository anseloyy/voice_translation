/**
 * Hardware Integration Module (for Raspberry Pi)
 * 
 * This module handles interaction with hardware components via WebSockets
 * It is only used in kiosk mode on the Raspberry Pi
 */

const hardwareController = (() => {
    // Private variables
    const _socket = io();
    let _isKioskMode = false;
    
    // Initialize event listeners for hardware events
    const initialize = () => {
        // Detect if running on Raspberry Pi (kiosk mode)
        _socket.on('system_status', (data) => {
            _isKioskMode = data.platform === 'raspberry_pi';
            console.log(`Running in ${_isKioskMode ? 'kiosk mode (Raspberry Pi)' : 'web mode'}`);
            
            if (_isKioskMode) {
                console.log('Hardware buttons are active');
                
                // Listen for button press events
                _socket.on('button_press', (data) => {
                    console.log(`Hardware button pressed: ${data.button}`);
                });
                
                // Listen for motion sensor events
                _socket.on('motion_detected', () => {
                    console.log('Motion detected by PIR sensor');
                });
            }
        });
    };
    
    /**
     * Simulate a button press (for testing)
     * @param {string} buttonType - Type of button to simulate
     */
    const simulateButtonPress = (buttonType) => {
        if (!_isKioskMode) {
            console.log(`Simulating button press: ${buttonType}`);
            
            // Emit the event as if it came from hardware
            const event = new CustomEvent('hardware_button', {
                detail: { button: buttonType }
            });
            document.dispatchEvent(event);
        } else {
            console.log('Cannot simulate button press in kiosk mode');
        }
    };
    
    /**
     * Simulate motion detection (for testing)
     */
    const simulateMotionDetection = () => {
        if (!_isKioskMode) {
            console.log('Simulating motion detection');
            
            // Emit the event as if it came from hardware
            const event = new CustomEvent('hardware_motion');
            document.dispatchEvent(event);
        } else {
            console.log('Cannot simulate motion detection in kiosk mode');
        }
    };
    
    // Initialize on load
    document.addEventListener('DOMContentLoaded', initialize);
    
    // Public API
    return {
        isKioskMode: () => _isKioskMode,
        simulateButtonPress,
        simulateMotionDetection
    };
})();
