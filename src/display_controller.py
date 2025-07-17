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
        
        # Display flight info with border
        try:
            # Draw border frame
            self._draw_border()
            
            # Line 1: Callsign (top line)
            self._draw_text(callsign[:16], 3, 8, config.ROW_ONE_COLOR)
            
            # Line 2: Aircraft and altitude (middle line)
            line2_text = f"{aircraft[:8]} {altitude}ft"
            self._draw_text(line2_text[:16], 3, 18, config.ROW_TWO_COLOR)
            
            # Line 3: Route (bottom line)
            self._draw_text(route[:16], 3, 28, config.ROW_THREE_COLOR)
            
            if config.DEBUG_MODE:
                print(f"Displayed flight: {callsign} - {aircraft} at {altitude}ft")
                
        except Exception as e:
            print(f"Error displaying flight info: {e}")
    
    def show_weather_info(self, weather_data: Dict[str, Any]):
        """
        Display weather and runway information with full-screen layout.
        
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
        
        try:
            # Draw border frame
            self._draw_border()
            
            # Layout for 128x32 display:
            # Top section (lines 2-10): Status and runway info
            # Middle section (lines 11-21): Weather icon and conditions
            # Bottom section (lines 22-30): METAR info
            
            # Top section: Status message
            self._draw_text("NO RWY04 ARRIVALS", 3, 3, config.ROW_ONE_COLOR)
            self._draw_text(f"ARR: RWY{arrivals}", 3, 8, config.ROW_TWO_COLOR)
            
            # Get weather conditions and draw appropriate icon
            weather_condition = self._parse_weather_condition(metar)
            self._draw_weather_icon(weather_condition, 3, 13)
            
            # Weather info next to icon
            wind_info = self._extract_wind_from_metar(metar)
            temp_info = self._extract_temperature_from_metar(metar)
            
            self._draw_text("METAR:", 25, 13, config.ROW_THREE_COLOR)
            self._draw_text(wind_info, 25, 18, config.ROW_THREE_COLOR)
            if temp_info:
                self._draw_text(temp_info, 25, 23, config.ROW_THREE_COLOR)
            
            # Visibility info on the right
            visibility = self._extract_visibility_from_metar(metar)
            if visibility:
                self._draw_text(f"VIS: {visibility}", 70, 18, config.ROW_ONE_COLOR)
            
            # Cloud info
            clouds = self._extract_clouds_from_metar(metar)
            if clouds:
                self._draw_text(clouds, 70, 23, config.ROW_TWO_COLOR)
            
            if config.DEBUG_MODE:
                print(f"Displayed weather: ARR={arrivals}, Weather={weather_condition}, Wind={wind_info}")
                
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
            # Draw border frame
            self._draw_border()
            
            # Display "no flights" message
            self._draw_text("RWY04 ACTIVE", 3, 8, config.ROW_ONE_COLOR)
            self._draw_text("No Approach", 3, 18, config.ROW_TWO_COLOR)
            self._draw_text("Traffic", 3, 28, config.ROW_THREE_COLOR)
            
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
    
    def _draw_border(self):
        """Draw a 1-pixel white border around the entire display."""
        if not self.hardware_ready:
            return
        
        # Top and bottom borders
        for x in range(self.matrix.width):
            self.matrix.SetPixel(x, 0, 255, 255, 255)  # Top
            self.matrix.SetPixel(x, self.matrix.height - 1, 255, 255, 255)  # Bottom
        
        # Left and right borders
        for y in range(self.matrix.height):
            self.matrix.SetPixel(0, y, 255, 255, 255)  # Left
            self.matrix.SetPixel(self.matrix.width - 1, y, 255, 255, 255)  # Right
    
    def _parse_weather_condition(self, metar: str) -> str:
        """Parse weather condition from METAR string."""
        if not metar:
            return "unknown"
        
        metar_upper = metar.upper()
        
        # Check for precipitation
        if any(precip in metar_upper for precip in ['RA', 'SHRA', 'TSRA', 'DZ']):
            return "rainy"
        elif any(precip in metar_upper for precip in ['SN', 'SHSN', 'BLSN']):
            return "snowy"
        elif any(precip in metar_upper for precip in ['TS', 'VCTS']):
            return "stormy"
        
        # Check for cloud coverage
        if any(cloud in metar_upper for cloud in ['OVC', 'BKN']):
            return "cloudy"
        elif any(cloud in metar_upper for cloud in ['SCT', 'FEW']):
            return "partly_cloudy"
        elif 'CLR' in metar_upper or 'SKC' in metar_upper:
            return "sunny"
        
        return "cloudy"  # Default
    
    def _draw_weather_icon(self, condition: str, x: int, y: int):
        """Draw a simple weather icon based on condition."""
        if not self.hardware_ready:
            return
        
        # Define weather icons (16x8 pixels)
        icons = {
            "sunny": [
                "   0111110   ",
                "  01111111  ",
                " 0111111111 ",
                "01111111111",
                "01111111111",
                " 0111111111 ",
                "  01111111  ",
                "   0111110   "
            ],
            "cloudy": [
                "   oooo     ",
                "  oooooo    ",
                " oooooooo   ",
                "oooooooooo  ",
                "oooooooooo  ",
                " oooooooo   ",
                "  oooooo    ",
                "   oooo     "
            ],
            "partly_cloudy": [
                "   0111 ooo ",
                "  01111oooo ",
                " 011111oooo ",
                "011111oooooo",
                "011111oooooo",
                " 01111oooo  ",
                "  0111 ooo  ",
                "   01   o   "
            ],
            "rainy": [
                "   oooo     ",
                "  oooooo    ",
                " oooooooo   ",
                "oooooooooo  ",
                "oooooooooo  ",
                " b b b b b  ",
                "  b b b b   ",
                " b b b b b  "
            ],
            "snowy": [
                "   oooo     ",
                "  oooooo    ",
                " oooooooo   ",
                "oooooooooo  ",
                "oooooooooo  ",
                " w w w w w  ",
                "  w w w w   ",
                " w w w w w  "
            ],
            "stormy": [
                "   oooo     ",
                "  oooooo    ",
                " oooooooo   ",
                "oooooooooo  ",
                "oooooooooo  ",
                " y  y  y  y ",
                "  y  y  y   ",
                " y  y  y  y "
            ]
        }
        
        if condition not in icons:
            condition = "cloudy"
        
        icon = icons[condition]
        
        # Color mapping
        colors = {
            '0': (255, 255, 0),    # Yellow (sun)
            'o': (128, 128, 128),  # Gray (clouds)
            'b': (0, 0, 255),      # Blue (rain)
            'w': (255, 255, 255),  # White (snow)
            'y': (255, 255, 0),    # Yellow (lightning)
            ' ': None              # Transparent
        }
        
        for row, line in enumerate(icon):
            for col, char in enumerate(line):
                if char in colors and colors[char]:
                    color = colors[char]
                    self.matrix.SetPixel(x + col, y + row, color[0], color[1], color[2])
    
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
    
    def _extract_temperature_from_metar(self, metar: str) -> str:
        """Extract temperature information from METAR string."""
        if not metar:
            return None
        
        try:
            # Look for temperature/dewpoint pattern like "29/22"
            temp_match = re.search(r'(\d+)/(\d+)', metar)
            if temp_match:
                temp = temp_match.group(1)
                return f"{temp}C"
            else:
                return None
        except Exception:
            return None
    
    def _extract_visibility_from_metar(self, metar: str) -> str:
        """Extract visibility information from METAR string."""
        if not metar:
            return None
        
        try:
            # Look for visibility pattern like "10SM"
            vis_match = re.search(r'(\d+)SM', metar)
            if vis_match:
                visibility = vis_match.group(1)
                return f"{visibility}SM"
            else:
                return None
        except Exception:
            return None
    
    def _extract_clouds_from_metar(self, metar: str) -> str:
        """Extract cloud information from METAR string."""
        if not metar:
            return None
        
        try:
            # Look for cloud patterns like "SCT025", "BKN120", etc.
            cloud_patterns = re.findall(r'(FEW|SCT|BKN|OVC)(\d+)', metar)
            if cloud_patterns:
                # Take the first significant cloud layer
                cloud_type, height = cloud_patterns[0]
                cloud_names = {
                    'FEW': 'Few',
                    'SCT': 'Scattered', 
                    'BKN': 'Broken',
                    'OVC': 'Overcast'
                }
                return f"{cloud_names.get(cloud_type, cloud_type)} {height}00ft"
            elif 'CLR' in metar or 'SKC' in metar:
                return "Clear"
            else:
                return None
        except Exception:
            return None
    
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