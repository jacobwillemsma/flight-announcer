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
        
        # For debugging: keep track of what's being displayed
        self.debug_display = []
        
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
        # Always initialize debug display for testing
        self._init_debug_display()
        
        # Clear the matrix if hardware is available
        if self.hardware_ready:
            self.matrix.Clear()
        
        # Extract flight information
        callsign = flight_data.get("callsign", "Unknown")
        aircraft = flight_data.get("aircraft_type", "")
        altitude = flight_data.get("altitude", 0)
        route = flight_data.get("route", "")
        
        # Display flight info with full screen space
        try:
            # Available space: 128x32 (full display)
            # Text positions with proper spacing
            
            # Line 1: Callsign (y=2)
            self._draw_text(callsign, 1, 2, config.ROW_ONE_COLOR)
            
            # Line 2: Aircraft and altitude (y=12, with 2px gap from previous line)
            line2_text = f"{aircraft} {altitude}ft"
            self._draw_text(line2_text, 1, 12, config.ROW_TWO_COLOR)
            
            # Line 3: Route (y=22, with 2px gap from previous line)
            self._draw_text(route, 1, 22, config.ROW_THREE_COLOR)
            
            # Always print debug display (both hardware and test mode)
            self._print_debug_display()
            
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
        # Always initialize debug display for testing
        self._init_debug_display()
        
        # Clear the matrix if hardware is available
        if self.hardware_ready:
            self.matrix.Clear()
        
        # Extract weather information
        arrivals = weather_data.get("arrivals_runway", "Unknown")
        departures = weather_data.get("departures_runway", "Unknown")
        metar = weather_data.get("metar", "Weather unavailable")
        
        try:
            # Layout for 128x32 display with full screen space:
            # Available space: 128x32 (full display)
            # Text positions with proper spacing
            
            # Top section: "Weather at LGA:" (y=2)
            line1_text = "Weather at LGA:"
            self._draw_text(line1_text, 1, 2, config.ROW_ONE_COLOR)
            
            # Bottom section: Weather icon (18x18) on left + temperature & wind on right
            # Draw weather icon starting at y=12 (lines 2&3 combined)
            weather_condition = self._parse_weather_condition(metar)
            self._draw_weather_icon(weather_condition, 1, 12)
            
            # Draw temperature and wind on same line to the right of the icon
            temperature = self._extract_temperature_from_metar(metar)
            wind_info = self._extract_wind_from_metar(metar)
            
            # Combine temperature and wind on same line
            temp_text = temperature if temperature else "Temp: N/A"
            if wind_info:
                combined_text = f"{temp_text} {wind_info}"
            else:
                combined_text = temp_text
            
            self._draw_text(combined_text, 24, 16, config.ROW_THREE_COLOR)  # Start at x=24, with 2px more padding from icon
            
            # Always print debug display (both hardware and test mode)
            self._print_debug_display()
            
            if config.DEBUG_MODE:
                print(f"Displayed weather: ARR={arrivals}, DEP={departures}, Temp={temperature if temperature else 'N/A'}")
                
        except Exception as e:
            print(f"Error displaying weather info: {e}")
    
    def show_no_flights_message(self, message_data: Dict[str, Any]):
        """Display message when no flights detected."""
        # Always initialize debug display for testing
        self._init_debug_display()
        
        # Clear the matrix if hardware is available
        if self.hardware_ready:
            self.matrix.Clear()
        
        try:
            # Available space: 128x32 (full display)
            # Text positions with proper spacing
            
            # Display "no flights" message with full screen space
            self._draw_text("No Approach", 1, 2, config.ROW_ONE_COLOR)
            self._draw_text("Traffic", 1, 12, config.ROW_TWO_COLOR)
            self._draw_text("Detected", 1, 22, config.ROW_THREE_COLOR)
            
            # Always print debug display (both hardware and test mode)
            self._print_debug_display()
            
            if config.DEBUG_MODE:
                print("Displayed: No Approach Traffic Detected")
                
        except Exception as e:
            print(f"Error displaying no flights message: {e}")
    
    def clear_display(self):
        """Clear the LED matrix display."""
        if self.hardware_ready:
            self.matrix.Clear()
        self._init_debug_display()
    
    def _init_debug_display(self):
        """Initialize debug display buffer."""
        # Create a 128x32 grid filled with spaces (off pixels)
        self.debug_display = []
        for y in range(32):
            self.debug_display.append([' ' for x in range(128)])
    
    def _set_debug_pixel(self, x: int, y: int, on: bool = True):
        """Set a pixel in the debug display."""
        if 0 <= x < 128 and 0 <= y < 32:
            self.debug_display[y][x] = '█' if on else ' '
    
    def _print_debug_display(self):
        """Print the current debug display to console."""
        print("\n" + "="*130)
        print("LED MATRIX DISPLAY OUTPUT (128x32) - Binary On/Off")
        print("="*130)
        
        for y, row in enumerate(self.debug_display):
            # Add line numbers for easier debugging
            line_num = f"{y:2d}"
            print(f"{line_num}│{''.join(row)}│")
        
        print("="*130)
        print("Legend: █ = LED on, ' ' = LED off")
        print("="*130)
    
    
    def _draw_text(self, text: str, x: int, y: int, color: tuple):
        """
        Draw text on the LED matrix using simple pixel patterns.
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: RGB color tuple
        """
        # Improved 5x8 font patterns for better readability
        patterns = {
            '0': [0b11111, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11111],
            '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
            '2': [0b11111, 0b00001, 0b00001, 0b11111, 0b10000, 0b10000, 0b10000, 0b11111],
            '3': [0b11111, 0b00001, 0b00001, 0b11111, 0b00001, 0b00001, 0b00001, 0b11111],
            '4': [0b10001, 0b10001, 0b10001, 0b11111, 0b00001, 0b00001, 0b00001, 0b00001],
            '5': [0b11111, 0b10000, 0b10000, 0b11111, 0b00001, 0b00001, 0b00001, 0b11111],
            '6': [0b11111, 0b10000, 0b10000, 0b11111, 0b10001, 0b10001, 0b10001, 0b11111],
            '7': [0b11111, 0b00001, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
            '8': [0b11111, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001, 0b11111],
            '9': [0b11111, 0b10001, 0b10001, 0b11111, 0b00001, 0b00001, 0b00001, 0b11111],
            'A': [0b11111, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001, 0b10001],
            'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110],
            'C': [0b11111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
            'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
            'E': [0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b10000, 0b11111],
            'F': [0b11111, 0b10000, 0b10000, 0b11111, 0b10000, 0b10000, 0b10000, 0b10000],
            'G': [0b11111, 0b10000, 0b10000, 0b10111, 0b10001, 0b10001, 0b10001, 0b11111],
            'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001, 0b10001],
            'I': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
            'J': [0b11111, 0b00001, 0b00001, 0b00001, 0b00001, 0b10001, 0b10001, 0b11111],
            'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001, 0b10001],
            'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
            'M': [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001],
            'N': [0b10001, 0b11001, 0b10101, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
            'O': [0b11111, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11111],
            'P': [0b11111, 0b10001, 0b10001, 0b11111, 0b10000, 0b10000, 0b10000, 0b10000],
            'Q': [0b11111, 0b10001, 0b10001, 0b10001, 0b10101, 0b10011, 0b10001, 0b11111],
            'R': [0b11111, 0b10001, 0b10001, 0b11111, 0b10100, 0b10010, 0b10001, 0b10001],
            'S': [0b11111, 0b10000, 0b10000, 0b11111, 0b00001, 0b00001, 0b00001, 0b11111],
            'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
            'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11111],
            'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b01010, 0b00100],
            'W': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10101, 0b11011, 0b10001],
            'X': [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001, 0b10001],
            'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
            'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b10000, 0b11111],
            ' ': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
            ':': [0b00000, 0b00100, 0b00100, 0b00000, 0b00000, 0b00100, 0b00100, 0b00000],
            '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000, 0b00000],
            '→': [0b00000, 0b00100, 0b00010, 0b11111, 0b00010, 0b00100, 0b00000, 0b00000],
            '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100],
            '@': [0b11111, 0b10001, 0b10101, 0b10111, 0b10110, 0b10000, 0b10000, 0b11111],
            '/': [0b00001, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b10000, 0b10000],
            '°': [0b01110, 0b10001, 0b10001, 0b01110, 0b00000, 0b00000, 0b00000, 0b00000],
        }
        
        char_x = x
        for char in text.upper():
            if char in patterns:
                pattern = patterns[char]
                for row in range(8):  # 8 rows for new font
                    for col in range(5):  # 5 columns for new font
                        if pattern[row] & (1 << (4-col)):  # Check from bit 4 to 0
                            if self.hardware_ready:
                                self.matrix.SetPixel(char_x + col, y + row, color[0], color[1], color[2])
                            self._set_debug_pixel(char_x + col, y + row, True)
                char_x += 6  # Move to next character position (5 pixels + 1 space)
            else:
                # Unknown character, skip
                char_x += 6
    
    
    
    
    
    def _extract_temperature_from_metar(self, metar: str) -> str:
        """Extract temperature information from METAR string."""
        if not metar:
            return None
        
        try:
            # Look for temperature/dewpoint pattern like "29/22"
            temp_match = re.search(r'(\d+)/(\d+)', metar)
            if temp_match:
                temp = temp_match.group(1)
                return f"{temp}°C"
            else:
                return None
        except Exception:
            return None
    
    def _extract_wind_from_metar(self, metar: str) -> str:
        """Extract wind information from METAR string."""
        if not metar:
            return None
        
        try:
            # Look for wind pattern like "18006KT" or "25009G19KT" (with optional gusts)
            wind_match = re.search(r'(\d{3})(\d{2,3})(?:G(\d{2,3}))?KT', metar)
            if wind_match:
                direction = wind_match.group(1)
                speed = wind_match.group(2).lstrip('0') or '0'
                gust = wind_match.group(3)
                
                if gust:
                    gust = gust.lstrip('0') or '0'
                    return f"{direction}@{speed}G{gust}kt"
                else:
                    return f"{direction}@{speed}kt"
            else:
                return None
        except Exception:
            return None
    
    
    
    
    
    
    
    
    
    
    

    def _parse_weather_condition(self, metar: str) -> str:
        """Parse weather condition from METAR string - simplified to 3 categories."""
        if not metar:
            return "cloudy"
        
        metar_upper = metar.upper()
        
        # Check for any precipitation (rain, snow, storms)
        if any(precip in metar_upper for precip in ['RA', 'SHRA', 'TSRA', 'DZ', 'SN', 'SHSN', 'BLSN', 'TS', 'VCTS']):
            return "rainy"
        
        # Check for clear/sunny conditions
        elif 'CLR' in metar_upper or 'SKC' in metar_upper:
            return "sunny"
        
        # Everything else defaults to cloudy (overcast/cloudy conditions)
        return "cloudy"
    
    def _draw_weather_icon(self, condition: str, x: int, y: int):
        """Draw emoji-like weather icons on the LED matrix."""
        
        # 18x18 pixel weather icons
        simple_icons = {
            "sunny": [
                "                  ",  # Row 0 - Empty
                " s      s      s  ",  # Row 1 - Top ray
                "  s     s     s   ",  # Row 2 - Diagonal rays
                "   s    s    s    ",  # Row 3 - Diagonal rays
                "                  ",  # Row 4 - Empty
                "     sssssss      ",  # Row 5 - Top of circle
                "    sssssssss     ",  # Row 6 - Circle sides
                "    sssssssss     ",  # Row 7 - Circle
                "    sssssssss     ",  # Row 8 - Circle
                "sss sssssssss  sss",  # Row 9 - Circle + left/right rays
                "    sssssssss     ",  # Row 10 - Circle
                "    sssssssss     ",  # Row 11 - Circle
                "    sssssssss     ",  # Row 12 - Circle sides
                "     sssssss      ",  # Row 13 - Bottom of circle
                "    s   s   s     ",  # Row 14 - Diagonal rays
                "   s    s    s    ",  # Row 15 - Diagonal rays
                "  s     s     s   ",  # Row 16 - Diagonal rays
                "                  ",  # Row 17 - Empty
            ],
            "cloudy": [
                "                  ",
                "                  ",
                "  ~~~~~~~~~~~~~~  ",
                "                  ",
                "                  ",
                "~~~~~~~~~~~~      ",
                "                  ",
                "                  ",
                "      ~~~~~~~~~~  ",
                "                  ",
                "                  ",
                "  ~~~~~~~~~~~~~~  ",
                "                  ",
                "                  ",
                "~~~~~~~~~~        ",
                "                  ",
                "                  ",
                "                  "
            ],
            "rainy": [
                "                  ",  # Row 0 - Empty
                "                  ",  # Row 1 - Empty
                "                  ",  # Row 1 - Empty
                "        o         ",  # Row 2 - Single point at top
                "       ooo        ",  # Row 3 - Start widening
                "      ooooo       ",  # Row 4 - Wider
                "     ooooooo      ",  # Row 5 - Wider
                "    ooooooooo     ",  # Row 6 - Wider
                "   ooooooooooo    ",  # Row 7 - Wider
                "  ooooooooooooo   ",  # Row 8 - Wider
                "  ooooooooooooo   ",  # Row 9 - Widest part (13 pixels)
                "  ooooooooooooo   ",  # Row 10 - Widest part (13 pixels)
                "   ooooooooooo    ",  # Row 11 - Widest part (13 pixels)
                "    ooooooooo     ",  # Row 12 - Start rounding (11 pixels)
                "     ooooooo      ",  # Row 13 - More rounded (9 pixels)
                "                  ",  # Row 15 - Rounded bottom (5 pixels)
                "                  ",  # Row 16 - Rounded bottom (3 pixels)
                "                  ",  # Row 17 - Empty
            ]
        }
        
        if condition not in simple_icons:
            condition = "cloudy"
        
        icon = simple_icons[condition]
        
        # Color mapping for weather elements
        colors = {
            's': (255, 200, 0),     # Yellow/orange (sun)
            'o': (0, 100, 255),     # Blue (rain drop)
            '~': (255, 255, 255),   # White (cloud lines)
            ' ': None               # Transparent
        }
        
        for row, line in enumerate(icon):
            for col, char in enumerate(line):
                if char in colors and colors[char]:
                    color = colors[char]
                    pixel_x = x + col
                    pixel_y = y + row
                    
                    # Make sure we don't go outside display bounds
                    if pixel_x < 128 and pixel_y < 32:
                        if self.hardware_ready:
                            self.matrix.SetPixel(pixel_x, pixel_y, color[0], color[1], color[2])
                        self._set_debug_pixel(pixel_x, pixel_y, True)

# Global instance for easy access
display_controller = DisplayController()