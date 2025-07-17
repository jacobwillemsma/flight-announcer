#!/usr/bin/env python3
"""
Display Controller
Handles LED matrix display operations using the rgbmatrix library.
Based on the working test_matrix.py configuration.
"""

import time
import sys
import os
import re
from typing import Dict, Any, Optional

# Add the library path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../lib/rpi-rgb-led-matrix/bindings/python'))

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Warning: rgbmatrix library not available - running in test mode")

try:
    import config
except ImportError:
    print("Error: Could not import config module")
    exit(1)

class DisplayController:
    """Handles LED matrix display operations."""
    
    def __init__(self):
        self.matrix = None
        self.hardware_ready = False
        
        if HARDWARE_AVAILABLE:
            self._init_hardware()
    
    def _init_hardware(self):
        """Initialize the LED matrix hardware."""
        try:
            # Configure matrix options (from working test_matrix.py)
            options = RGBMatrixOptions()
            options.rows = config.MATRIX_ROWS
            options.cols = config.MATRIX_COLS
            options.chain_length = config.MATRIX_CHAIN_LENGTH
            options.parallel = config.MATRIX_PARALLEL
            options.hardware_mapping = config.MATRIX_HARDWARE_MAPPING
            
            self.matrix = RGBMatrix(options=options)
            self.hardware_ready = True
            
            if config.DEBUG_MODE:
                print(f"LED Matrix initialized: {self.matrix.width}x{self.matrix.height}")
            
        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.hardware_ready = False
    
    def show_flight_info(self, flight_data: Dict[str, Any]):
        """
        Display flight information on the LED matrix.
        
        Args:
            flight_data: Flight data dictionary
        """
        if not self.hardware_ready:
            self._print_flight_info(flight_data)
            return
        
        # Clear the matrix
        self.matrix.Clear()
        
        # Extract flight information
        callsign = flight_data.get("callsign", "Unknown")
        aircraft = flight_data.get("aircraft_type", "")
        altitude = flight_data.get("altitude", 0)
        route = flight_data.get("route", "")
        
        # Display flight info on 3 lines
        try:
            # Line 1: Callsign (top line)
            self._draw_text(callsign[:16], 1, 8, config.ROW_ONE_COLOR)
            
            # Line 2: Aircraft and altitude (middle line)
            line2_text = f"{aircraft[:8]} {altitude}ft"
            self._draw_text(line2_text[:16], 1, 18, config.ROW_TWO_COLOR)
            
            # Line 3: Route (bottom line)
            self._draw_text(route[:16], 1, 28, config.ROW_THREE_COLOR)
            
            if config.DEBUG_MODE:
                print(f"Displayed flight: {callsign} - {aircraft} at {altitude}ft")
                
        except Exception as e:
            print(f"Error displaying flight info: {e}")
    
    def show_weather_info(self, weather_data: Dict[str, Any]):
        """
        Display weather and runway information.
        
        Args:
            weather_data: Weather data dictionary
        """
        if not self.hardware_ready:
            self._print_weather_info(weather_data)
            return
        
        # Clear the matrix
        self.matrix.Clear()
        
        # Extract weather information
        arrivals = weather_data.get("arrivals_runway", "Unknown")
        departures = weather_data.get("departures_runway", "Unknown")
        metar = weather_data.get("metar", "Weather unavailable")
        
        # Extract wind information from METAR
        wind_info = self._extract_wind_from_metar(metar)
        
        try:
            # Line 1: Arrivals runway
            self._draw_text(f"ARR: RWY{arrivals}", 1, 8, config.ROW_ONE_COLOR)
            
            # Line 2: Departures runway
            self._draw_text(f"DEP: RWY{departures}", 1, 18, config.ROW_TWO_COLOR)
            
            # Line 3: Wind information
            self._draw_text(wind_info[:16], 1, 28, config.ROW_THREE_COLOR)
            
            if config.DEBUG_MODE:
                print(f"Displayed weather: ARR={arrivals}, DEP={departures}, Wind={wind_info}")
                
        except Exception as e:
            print(f"Error displaying weather info: {e}")
    
    def show_no_flights_message(self, message_data: Dict[str, Any]):
        """Display message when RWY04 active but no flights."""
        if not self.hardware_ready:
            print(message_data.get("message", "No flights"))
            return
        
        # Clear the matrix
        self.matrix.Clear()
        
        try:
            # Display "no flights" message
            self._draw_text("RWY04 ACTIVE", 1, 8, config.ROW_ONE_COLOR)
            self._draw_text("No Approach", 1, 18, config.ROW_TWO_COLOR)
            self._draw_text("Traffic", 1, 28, config.ROW_THREE_COLOR)
            
            if config.DEBUG_MODE:
                print("Displayed: RWY04 Active - No Approach Traffic")
                
        except Exception as e:
            print(f"Error displaying no flights message: {e}")
    
    def clear_display(self):
        """Clear the LED matrix display."""
        if not self.hardware_ready:
            print("Display cleared")
            return
        
        self.matrix.Clear()
    
    def _draw_text(self, text: str, x: int, y: int, color: tuple):
        """
        Draw text on the LED matrix using simple pixel patterns.
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: RGB color tuple
        """
        if not self.hardware_ready:
            return
        
        # Simple 3x5 font patterns for basic characters
        patterns = {
            '0': [0b111, 0b101, 0b101, 0b101, 0b111],
            '1': [0b001, 0b001, 0b001, 0b001, 0b001],
            '2': [0b111, 0b001, 0b111, 0b100, 0b111],
            '3': [0b111, 0b001, 0b111, 0b001, 0b111],
            '4': [0b101, 0b101, 0b111, 0b001, 0b001],
            '5': [0b111, 0b100, 0b111, 0b001, 0b111],
            '6': [0b111, 0b100, 0b111, 0b101, 0b111],
            '7': [0b111, 0b001, 0b001, 0b001, 0b001],
            '8': [0b111, 0b101, 0b111, 0b101, 0b111],
            '9': [0b111, 0b101, 0b111, 0b001, 0b111],
            'A': [0b111, 0b101, 0b111, 0b101, 0b101],
            'B': [0b110, 0b101, 0b110, 0b101, 0b110],
            'C': [0b111, 0b100, 0b100, 0b100, 0b111],
            'D': [0b110, 0b101, 0b101, 0b101, 0b110],
            'E': [0b111, 0b100, 0b111, 0b100, 0b111],
            'F': [0b111, 0b100, 0b111, 0b100, 0b100],
            'G': [0b111, 0b100, 0b101, 0b101, 0b111],
            'H': [0b101, 0b101, 0b111, 0b101, 0b101],
            'I': [0b111, 0b010, 0b010, 0b010, 0b111],
            'J': [0b111, 0b001, 0b001, 0b101, 0b111],
            'K': [0b101, 0b110, 0b100, 0b110, 0b101],
            'L': [0b100, 0b100, 0b100, 0b100, 0b111],
            'M': [0b101, 0b111, 0b111, 0b101, 0b101],
            'N': [0b101, 0b111, 0b111, 0b111, 0b101],
            'O': [0b111, 0b101, 0b101, 0b101, 0b111],
            'P': [0b111, 0b101, 0b111, 0b100, 0b100],
            'Q': [0b111, 0b101, 0b101, 0b111, 0b001],
            'R': [0b111, 0b101, 0b111, 0b110, 0b101],
            'S': [0b111, 0b100, 0b111, 0b001, 0b111],
            'T': [0b111, 0b010, 0b010, 0b010, 0b010],
            'U': [0b101, 0b101, 0b101, 0b101, 0b111],
            'V': [0b101, 0b101, 0b101, 0b101, 0b010],
            'W': [0b101, 0b101, 0b111, 0b111, 0b101],
            'X': [0b101, 0b101, 0b010, 0b101, 0b101],
            'Y': [0b101, 0b101, 0b010, 0b010, 0b010],
            'Z': [0b111, 0b001, 0b010, 0b100, 0b111],
            ' ': [0b000, 0b000, 0b000, 0b000, 0b000],
            ':': [0b000, 0b010, 0b000, 0b010, 0b000],
            '-': [0b000, 0b000, 0b111, 0b000, 0b000],
            '→': [0b001, 0b011, 0b111, 0b011, 0b001],
            '.': [0b000, 0b000, 0b000, 0b000, 0b100],
        }
        
        char_x = x
        for char in text.upper():
            if char in patterns:
                pattern = patterns[char]
                for row in range(5):
                    for col in range(3):
                        if pattern[row] & (1 << (2-col)):
                            self.matrix.SetPixel(char_x + col, y + row, color[0], color[1], color[2])
                char_x += 4  # Move to next character position
            else:
                # Unknown character, skip
                char_x += 4
    
    def _extract_wind_from_metar(self, metar: str) -> str:
        """Extract wind information from METAR string."""
        if not metar:
            return "No wind data"
        
        try:
            # Look for wind pattern like "18006KT"
            wind_match = re.search(r'(\d{3})(\d{2,3})KT', metar)
            if wind_match:
                direction = wind_match.group(1)
                speed = wind_match.group(2).lstrip('0') or '0'
                return f"{direction}@{speed}kt"
            else:
                return "Wind unavailable"
        except Exception:
            return "Wind error"
    
    def _print_flight_info(self, flight_data: Dict[str, Any]):
        """Print flight info to console when hardware not available."""
        callsign = flight_data.get("callsign", "Unknown")
        aircraft = flight_data.get("aircraft_type", "")
        altitude = flight_data.get("altitude", 0)
        route = flight_data.get("route", "")
        
        print("=" * 50)
        print(f"FLIGHT DISPLAY")
        print(f"Callsign: {callsign}")
        print(f"Aircraft: {aircraft} at {altitude} feet")
        print(f"Route: {route}")
        print("=" * 50)
    
    def _print_weather_info(self, weather_data: Dict[str, Any]):
        """Print weather info to console when hardware not available."""
        arrivals = weather_data.get("arrivals_runway", "Unknown")
        departures = weather_data.get("departures_runway", "Unknown")
        metar = weather_data.get("metar", "Weather unavailable")
        
        print("=" * 50)
        print(f"WEATHER DISPLAY")
        print(f"Arrivals: RWY{arrivals}")
        print(f"Departures: RWY{departures}")
        print(f"METAR: {metar}")
        print("=" * 50)

# Global instance for easy access
display_controller = DisplayController()