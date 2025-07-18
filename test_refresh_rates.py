#!/usr/bin/env python3
"""
Refresh Rate Test Suite
Cycles through different refresh rates to test phone camera compatibility.
"""

import time
import sys
import os
import signal
from datetime import datetime

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from display_controller import DisplayController
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

class RefreshRateTestSuite:
    """Test suite that cycles through different refresh rates."""
    
    def __init__(self):
        self.running = True
        self.test_rates = list(range(30, 61))  # Hz to test: 30, 31, 32, ..., 60
        self.test_duration = 5  # seconds per test
        self.current_rate_index = 0
        self.matrix = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def _init_matrix_with_rate(self, refresh_rate):
        """Initialize matrix with specific refresh rate."""
        try:
            # Configure matrix options
            options = RGBMatrixOptions()
            options.rows = config.MATRIX_ROWS
            options.cols = config.MATRIX_COLS
            options.chain_length = config.MATRIX_CHAIN_LENGTH
            options.parallel = config.MATRIX_PARALLEL
            options.hardware_mapping = config.MATRIX_HARDWARE_MAPPING
            
            # Camera-friendly settings
            options.pwm_bits = config.PWM_BITS
            options.brightness = config.BRIGHTNESS
            options.pwm_lsb_nanoseconds = config.PWM_LSB_NANOSECONDS
            options.gpio_slowdown = config.GPIO_SLOWDOWN
            
            # Set the specific refresh rate for this test
            options.limit_refresh_rate_hz = refresh_rate
            options.disable_hardware_pulsing = config.DISABLE_HARDWARE_PULSING
            options.show_refresh_rate = True
            
            # Clean up old matrix if exists
            if self.matrix:
                del self.matrix
                time.sleep(0.1)
            
            self.matrix = RGBMatrix(options=options)
            
            print(f"Matrix initialized with {refresh_rate}Hz refresh rate")
            return True
            
        except Exception as e:
            print(f"Failed to initialize matrix with {refresh_rate}Hz: {e}")
            return False
    
    def _draw_test_pattern(self, refresh_rate):
        """Draw test pattern showing current refresh rate."""
        if not self.matrix:
            return
        
        # Clear display
        self.matrix.Clear()
        
        # Draw simple test pattern with refresh rate info
        # Line 1: "REFRESH TEST"
        self._draw_text("REFRESH TEST", 2, 4, (255, 255, 255))
        
        # Line 2: Current refresh rate
        rate_text = f"{refresh_rate}Hz"
        self._draw_text(rate_text, 2, 14, (255, 165, 0))
        
        # Line 3: Instruction
        self._draw_text("TEST CAMERA", 2, 24, (0, 255, 0))
    
    def _draw_text(self, text, x, y, color):
        """Draw text on the matrix (simple pixel font)."""
        if not self.matrix:
            return
        
        # Simple 5x8 font patterns for basic characters
        patterns = {
            'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001, 0b00000],
            'E': [0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b11111, 0b00000],
            'F': [0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b10000, 0b00000],
            'S': [0b11111, 0b10000, 0b10000, 0b11111, 0b00001, 0b00001, 0b11111, 0b00000],
            'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001, 0b00000],
            'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000],
            'C': [0b11111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111, 0b00000],
            'A': [0b11111, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001, 0b00000],
            'M': [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001, 0b00000],
            '0': [0b11111, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11111, 0b00000],
            '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111, 0b00000],
            '2': [0b11111, 0b00001, 0b00001, 0b11111, 0b10000, 0b10000, 0b11111, 0b00000],
            '3': [0b11111, 0b00001, 0b00001, 0b11111, 0b00001, 0b00001, 0b11111, 0b00000],
            '4': [0b10001, 0b10001, 0b10001, 0b11111, 0b00001, 0b00001, 0b00001, 0b00000],
            '5': [0b11111, 0b10000, 0b10000, 0b11111, 0b00001, 0b00001, 0b11111, 0b00000],
            '6': [0b11111, 0b10000, 0b10000, 0b11111, 0b10001, 0b10001, 0b11111, 0b00000],
            '7': [0b11111, 0b00001, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b00000],
            '8': [0b11111, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b11111, 0b00000],
            '9': [0b11111, 0b10001, 0b10001, 0b11111, 0b00001, 0b00001, 0b11111, 0b00000],
            ' ': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
        }
        
        char_x = x
        for char in text.upper():
            if char in patterns:
                pattern = patterns[char]
                for row in range(8):
                    for col in range(5):
                        if pattern[row] & (1 << (4-col)):
                            if (char_x + col < config.DISPLAY_WIDTH and 
                                y + row < config.DISPLAY_HEIGHT):
                                self.matrix.SetPixel(char_x + col, y + row, 
                                                   color[0], color[1], color[2])
                char_x += 6  # Move to next character position
            else:
                char_x += 6  # Skip unknown characters
    
    def run(self):
        """Run the refresh rate test suite."""
        print("=" * 60)
        print("Refresh Rate Test Suite")
        print("=" * 60)
        print(f"Testing refresh rates: {self.test_rates} Hz")
        print(f"Duration per test: {self.test_duration} seconds")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        try:
            while self.running:
                # Get current refresh rate to test
                current_rate = self.test_rates[self.current_rate_index]
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testing {current_rate}Hz...")
                
                # Initialize matrix with current refresh rate
                if self._init_matrix_with_rate(current_rate):
                    # Draw test pattern
                    self._draw_test_pattern(current_rate)
                    
                    # Wait for test duration
                    for i in range(self.test_duration):
                        if not self.running:
                            break
                        print(f"  {current_rate}Hz test: {i+1}/{self.test_duration} seconds")
                        time.sleep(1)
                    
                    # Move to next refresh rate
                    self.current_rate_index = (self.current_rate_index + 1) % len(self.test_rates)
                else:
                    print(f"Failed to test {current_rate}Hz, skipping...")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        if self.matrix:
            self.matrix.Clear()
            del self.matrix
        print("Refresh rate test suite stopped")

def main():
    """Main entry point."""
    test_suite = RefreshRateTestSuite()
    test_suite.run()

if __name__ == "__main__":
    main()