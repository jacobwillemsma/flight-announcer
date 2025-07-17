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
        
        # For alternating text display
        self.weather_line1_start_time = time.time()
        self.weather_line1_showing_first = True
        
        # For line 2 alternating and scrolling
        self.weather_line2_start_time = time.time()
        self.weather_line2_showing_runway = True
        self.scroll_state = {
            'text': '',
            'position': 0,
            'phase': 'pause_start',  # pause_start, scrolling, pause_end
            'phase_start_time': 0,
            'max_width': 126
        }
        
        # For line 3 METAR scrolling
        self.metar_scroll_state = {
            'text': '',
            'position': 0,
            'phase': 'pause_start',  # pause_start, scrolling, pause_end
            'phase_start_time': 0,
            'max_width': 126,
            'initialized': False
        }
        
        # Phonetic alphabet mapping
        self.phonetic_alphabet = {
            'A': 'ALPHA', 'B': 'BRAVO', 'C': 'CHARLIE', 'D': 'DELTA',
            'E': 'ECHO', 'F': 'FOXTROT', 'G': 'GOLF', 'H': 'HOTEL',
            'I': 'INDIA', 'J': 'JULIET', 'K': 'KILO', 'L': 'LIMA',
            'M': 'MIKE', 'N': 'NOVEMBER', 'O': 'OSCAR', 'P': 'PAPA',
            'Q': 'QUEBEC', 'R': 'ROMEO', 'S': 'SIERRA', 'T': 'TANGO',
            'U': 'UNIFORM', 'V': 'VICTOR', 'W': 'WHISKEY', 'X': 'XRAY',
            'Y': 'YANKEE', 'Z': 'ZULU'
        }
        
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
            self._draw_text_with_scroll(callsign, 1, 2, config.ROW_ONE_COLOR, 126)
            
            # Line 2: Aircraft and altitude (y=12, with 2px gap from previous line)
            line2_text = f"{aircraft} {altitude}ft"
            self._draw_text_with_scroll(line2_text, 1, 12, config.ROW_TWO_COLOR, 126)
            
            # Line 3: Route (y=22, with 2px gap from previous line)
            self._draw_text_with_scroll(route, 1, 22, config.ROW_THREE_COLOR, 126)
            
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
            
            # Top section: Alternating status message (y=2)
            line1_text = self._get_alternating_weather_line1()
            self._draw_text_with_scroll(line1_text, 1, 2, config.ROW_ONE_COLOR, 126)
            
            # Second line: Alternating runway info and ATIS information (y=12, with 2px gap from previous line)
            line2_text = self._get_alternating_weather_line2(arrivals, departures, metar)
            self._draw_text_with_scroll(line2_text, 1, 12, config.ROW_TWO_COLOR, 126)
            
            # Third line: Scrolling METAR (y=22, with 2px gap from previous line)
            line3_text = self._get_scrolling_metar(metar)
            self._draw_text_with_scroll(line3_text, 1, 22, config.ROW_THREE_COLOR, 126)
            
            # Always print debug display (both hardware and test mode)
            self._print_debug_display()
            
            if config.DEBUG_MODE:
                print(f"Displayed weather: ARR={arrivals}, Weather={weather_condition}, Wind={wind_info}")
                
        except Exception as e:
            print(f"Error displaying weather info: {e}")
    
    def show_no_flights_message(self, message_data: Dict[str, Any]):
        """Display message when RWY04 active but no flights."""
        # Always initialize debug display for testing
        self._init_debug_display()
        
        # Clear the matrix if hardware is available
        if self.hardware_ready:
            self.matrix.Clear()
        
        try:
            # Available space: 128x32 (full display)
            # Text positions with proper spacing
            
            # Display "no flights" message with full screen space
            self._draw_text_with_scroll("RWY04 ACTIVE", 1, 2, config.ROW_ONE_COLOR, 126)
            self._draw_text_with_scroll("No Approach", 1, 12, config.ROW_TWO_COLOR, 126)
            self._draw_text_with_scroll("Traffic", 1, 22, config.ROW_THREE_COLOR, 126)
            
            # Always print debug display (both hardware and test mode)
            self._print_debug_display()
            
            if config.DEBUG_MODE:
                print("Displayed: RWY04 Active - No Approach Traffic")
                
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
    
    def _draw_text_with_scroll(self, text: str, x: int, y: int, color: tuple, max_width: int):
        """
        Draw text with overflow detection and scrolling.
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: RGB color tuple
            max_width: Maximum width available for text
        """
        # Calculate text width (6 pixels per character)
        text_width = len(text) * 6 - 1  # -1 because no space after last character
        
        if text_width <= max_width:
            # Text fits, draw normally
            self._draw_text(text, x, y, color)
        else:
            # Text overflows, scroll it
            self._scroll_text(text, x, y, color, max_width)
    
    def _scroll_text(self, text: str, x: int, y: int, color: tuple, max_width: int):
        """Scroll text that overflows the available width."""
        # For now, just truncate long text to fit (will implement scrolling later)
        # Calculate how many characters can fit
        max_chars = (max_width + 1) // 6  # +1 to account for spacing
        if len(text) > max_chars:
            text = text[:max_chars-3] + "..."
        
        self._draw_text(text, x, y, color)
    
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
    
    def _draw_border(self):
        """Draw a 1-pixel white border around the entire display."""
        # Use config dimensions for consistent behavior
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT
        
        # Top and bottom borders
        for x in range(width):
            if self.hardware_ready:
                self.matrix.SetPixel(x, 0, 255, 255, 255)  # Top
                self.matrix.SetPixel(x, height - 1, 255, 255, 255)  # Bottom
            self._set_debug_pixel(x, 0, True)  # Top debug border
            self._set_debug_pixel(x, height - 1, True)  # Bottom debug border
        
        # Left and right borders
        for y in range(height):
            if self.hardware_ready:
                self.matrix.SetPixel(0, y, 255, 255, 255)  # Left
                self.matrix.SetPixel(width - 1, y, 255, 255, 255)  # Right
            self._set_debug_pixel(0, y, True)  # Left debug border
            self._set_debug_pixel(width - 1, y, True)  # Right debug border
    
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
                    if self.hardware_ready:
                        self.matrix.SetPixel(x + col, y + row, color[0], color[1], color[2])
                    self._set_debug_pixel(x + col, y + row, True)
    
    def _extract_wind_from_metar(self, metar: str) -> str:
        """Extract wind information from METAR string."""
        if not metar:
            return "No wind data"
        
        try:
            # Look for wind pattern like "18006KT" or "25009G19KT" (with optional gusts)
            wind_match = re.search(r'(\d{3})(\d{2,3})(?:G\d{2,3})?KT', metar)
            if wind_match:
                direction = wind_match.group(1)
                speed = wind_match.group(2).lstrip('0') or '0'
                return f"{direction}@{speed}kt"
            else:
                return "Wind unavailable"
        except Exception as e:
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
    
    def _get_alternating_weather_line1(self) -> str:
        """Get alternating text for weather display line 1."""
        current_time = time.time()
        
        # Check if 3 seconds have passed
        if current_time - self.weather_line1_start_time >= 5.0:
            self.weather_line1_showing_first = not self.weather_line1_showing_first
            self.weather_line1_start_time = current_time
        
        if self.weather_line1_showing_first:
            return "NO RWY 04 ARRIVALS"
        else:
            return "WEATHER AT KLGA"
    
    def _extract_atis_info_letter(self, metar: str) -> str:
        """Extract ATIS information letter from actual ATIS feed."""
        try:
            # Import here to avoid circular imports
            from lga_client import get_atis_text
            
            # Get the actual ATIS text
            atis_text = get_atis_text()
            if not atis_text:
                return "A"  # Fallback if ATIS unavailable
            
            # Look for "INFO X" pattern in ATIS text
            # Example: "LGA ATIS INFO H 1851Z" or "ADVS YOU HAVE INFO H"
            import re
            info_match = re.search(r'INFO\s+([A-Z])', atis_text.upper())
            if info_match:
                return info_match.group(1)
            
            # Fallback: try to find it at the end "ADVS YOU HAVE INFO X"
            advs_match = re.search(r'ADVS YOU HAVE INFO\s+([A-Z])', atis_text.upper())
            if advs_match:
                return advs_match.group(1)
                
        except Exception as e:
            print(f"Error extracting ATIS info letter: {e}")
            
        return "A"  # Default fallback
    
    def _get_alternating_weather_line2(self, arrivals: str, departures: str, metar: str) -> str:
        """Get alternating text for weather display line 2."""
        current_time = time.time()
        
        # Handle line 2 timing separately - more complex due to scrolling
        if self.weather_line2_showing_runway:
            # Currently showing runway info - check if 3 seconds have passed
            if current_time - self.weather_line2_start_time >= 3.0:
                # Switch to ATIS info and start scrolling
                self.weather_line2_showing_runway = False
                self.weather_line2_start_time = current_time
                
                # Initialize scroll state for ATIS info
                atis_letter = self._extract_atis_info_letter(metar)
                phonetic = self.phonetic_alphabet.get(atis_letter, "ALPHA")
                self.scroll_state['text'] = f"YOU HAVE INFORMATION {phonetic} "
                self.scroll_state['position'] = 0
                self.scroll_state['phase'] = 'pause_start'
                self.scroll_state['phase_start_time'] = current_time
        else:
            # Currently showing ATIS info - check if scrolling cycle is complete
            if self._is_scrolling_complete():
                # Switch back to runway info
                self.weather_line2_showing_runway = True
                self.weather_line2_start_time = current_time
        
        if self.weather_line2_showing_runway:
            return f"ARR: {arrivals}, DEP: {departures}"
        else:
            return self._get_scrolling_text()
    
    def _is_scrolling_complete(self) -> bool:
        """Check if the scrolling cycle is complete."""
        current_time = time.time()
        text = self.scroll_state['text']
        max_chars = self.scroll_state['max_width'] // 6
        
        # If text fits completely, it's "complete" after 3 seconds
        if len(text) <= max_chars:
            return current_time - self.scroll_state['phase_start_time'] >= 3.0
        
        # If we're in pause_end phase and have been there for 2 seconds, we're done
        if (self.scroll_state['phase'] == 'pause_end' and 
            current_time - self.scroll_state['phase_start_time'] >= 2.0):
            return True
        
        return False
    
    def _get_scrolling_text(self) -> str:
        """Get the current scrolling text based on scroll state."""
        current_time = time.time()
        text = self.scroll_state['text']
        max_width = self.scroll_state['max_width']
        
        # Calculate how many characters fit (6 pixels per character)
        max_chars = max_width // 6
        
        if len(text) <= max_chars:
            # Text fits completely, no scrolling needed
            return text
        
        phase_duration = current_time - self.scroll_state['phase_start_time']
        
        if self.scroll_state['phase'] == 'pause_start':
            # Show beginning of text for 2 seconds
            if phase_duration >= 2.0:
                self.scroll_state['phase'] = 'scrolling'
                self.scroll_state['phase_start_time'] = current_time
            return text[:max_chars]
        
        elif self.scroll_state['phase'] == 'scrolling':
            # Scroll one character at a time (every 200ms)
            chars_to_scroll = int(phase_duration / 0.2)
            self.scroll_state['position'] = min(chars_to_scroll, len(text) - max_chars)
            
            if self.scroll_state['position'] >= len(text) - max_chars:
                # Reached end, switch to pause
                self.scroll_state['phase'] = 'pause_end'
                self.scroll_state['phase_start_time'] = current_time
            
            start_pos = self.scroll_state['position']
            return text[start_pos:start_pos + max_chars]
        
        elif self.scroll_state['phase'] == 'pause_end':
            # Show end of text for 2 seconds
            # Don't reset here - let _is_scrolling_complete handle the transition
            return text[-max_chars:]
        
        return text[:max_chars]
    
    def _get_scrolling_metar(self, metar: str) -> str:
        """Get the current scrolling METAR text."""
        current_time = time.time()
        
        # Clean METAR by removing RMK section (remarks)
        cleaned_metar = self._clean_metar_for_weather(metar)
        
        # Initialize or update METAR text if changed
        if not self.metar_scroll_state['initialized'] or self.metar_scroll_state['text'] != cleaned_metar:
            self.metar_scroll_state['text'] = cleaned_metar
            self.metar_scroll_state['position'] = 0
            self.metar_scroll_state['phase'] = 'pause_start'
            self.metar_scroll_state['phase_start_time'] = current_time
            self.metar_scroll_state['initialized'] = True
        
        text = self.metar_scroll_state['text']
        max_width = self.metar_scroll_state['max_width']
        
        # Calculate how many characters fit (6 pixels per character)
        max_chars = max_width // 6
        
        if len(text) <= max_chars:
            # Text fits completely, no scrolling needed
            return text
        
        phase_duration = current_time - self.metar_scroll_state['phase_start_time']
        
        if self.metar_scroll_state['phase'] == 'pause_start':
            # Show beginning of text for 2 seconds
            if phase_duration >= 2.0:
                self.metar_scroll_state['phase'] = 'scrolling'
                self.metar_scroll_state['phase_start_time'] = current_time
            return text[:max_chars]
        
        elif self.metar_scroll_state['phase'] == 'scrolling':
            # Scroll one character at a time (every 200ms)
            chars_to_scroll = int(phase_duration / 0.2)
            self.metar_scroll_state['position'] = min(chars_to_scroll, len(text) - max_chars)
            
            if self.metar_scroll_state['position'] >= len(text) - max_chars:
                # Reached end, switch to pause
                self.metar_scroll_state['phase'] = 'pause_end'
                self.metar_scroll_state['phase_start_time'] = current_time
            
            start_pos = self.metar_scroll_state['position']
            return text[start_pos:start_pos + max_chars]
        
        elif self.metar_scroll_state['phase'] == 'pause_end':
            # Show end of text for 2 seconds, then restart
            if phase_duration >= 2.0:
                # Restart the cycle
                self.metar_scroll_state['position'] = 0
                self.metar_scroll_state['phase'] = 'pause_start'
                self.metar_scroll_state['phase_start_time'] = current_time
            return text[-max_chars:]
        
        return text[:max_chars]
    
    def _clean_metar_for_weather(self, metar: str) -> str:
        """Clean METAR string to show only weather information, excluding remarks."""
        if not metar:
            return "No METAR available"
        
        try:
            # Remove RMK section and everything after it
            if " RMK " in metar:
                metar = metar.split(" RMK ")[0]
            
            # Also remove trailing $ if present
            if metar.endswith(" $"):
                metar = metar[:-2]
            
            # Clean up any extra whitespace
            metar = " ".join(metar.split())
            
            return metar
            
        except Exception:
            return metar  # Return original if cleaning fails
    
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