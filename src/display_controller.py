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
    from flight_logic import CANADIAN_AIRPORTS
except ImportError:
    print("Error: Could not import config module")
    exit(1)

class DisplayController:
    """Handles LED matrix display operations with double buffering and selective updating."""
    
    def __init__(self):
        self.matrix = None
        self.hardware_ready = False
        
        # Double buffering system
        self.front_buffer = None
        self.back_buffer = None
        
        # Selective update tracking
        self.dirty_pixels = set()  # Set of (x, y) coordinates that need updating
        self.dirty_regions = []    # List of (x, y, width, height) regions that need updating
        
        # For debugging: keep track of what's being displayed
        self.debug_display = []
        
        if HARDWARE_AVAILABLE:
            self._init_hardware()
        
        # Initialize buffers
        self._init_buffers()
    
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
    
    def _init_buffers(self):
        """Initialize double buffering system."""
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT
        
        # Initialize front and back buffers as 2D arrays of RGB tuples
        self.front_buffer = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        self.back_buffer = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        # Clear dirty tracking
        self.dirty_pixels.clear()
        self.dirty_regions.clear()
        
        if config.DEBUG_MODE:
            print(f"Double buffers initialized: {width}x{height}")
    
    def _set_pixel_buffer(self, x: int, y: int, color: tuple, buffer=None):
        """Set a pixel in the specified buffer (defaults to back buffer)."""
        if buffer is None:
            buffer = self.back_buffer
        
        if 0 <= x < config.DISPLAY_WIDTH and 0 <= y < config.DISPLAY_HEIGHT:
            buffer[y][x] = color
            # Mark pixel as dirty for selective updating
            self.dirty_pixels.add((x, y))
    
    def _clear_buffer(self, buffer=None):
        """Clear the specified buffer (defaults to back buffer)."""
        if buffer is None:
            buffer = self.back_buffer
        
        width = config.DISPLAY_WIDTH
        height = config.DISPLAY_HEIGHT
        
        for y in range(height):
            for x in range(width):
                buffer[y][x] = (0, 0, 0)
                self.dirty_pixels.add((x, y))
    
    def _add_dirty_region(self, x: int, y: int, width: int, height: int):
        """Add a rectangular region to be updated."""
        self.dirty_regions.append((x, y, width, height))
        
        # Also add individual pixels to dirty set for fine-grained control
        for dy in range(height):
            for dx in range(width):
                px, py = x + dx, y + dy
                if 0 <= px < config.DISPLAY_WIDTH and 0 <= py < config.DISPLAY_HEIGHT:
                    self.dirty_pixels.add((px, py))
    
    def _swap_buffers(self):
        """Swap front and back buffers and update only dirty pixels."""
        if not self.hardware_ready:
            # In test mode, just swap the buffers
            self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
            self.dirty_pixels.clear()
            self.dirty_regions.clear()
            return
        
        # Update only dirty pixels on the hardware
        updated_pixels = 0
        for x, y in self.dirty_pixels:
            if 0 <= x < config.DISPLAY_WIDTH and 0 <= y < config.DISPLAY_HEIGHT:
                color = self.back_buffer[y][x]
                self.matrix.SetPixel(x, y, color[0], color[1], color[2])
                updated_pixels += 1
        
        # Swap buffers
        self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
        
        # Clear dirty tracking
        self.dirty_pixels.clear()
        self.dirty_regions.clear()
        
        if config.DEBUG_MODE and updated_pixels > 0:
            print(f"Selective update: {updated_pixels} pixels updated")
    
    def _force_full_update(self):
        """Force a complete display update (useful for initialization)."""
        if not self.hardware_ready:
            return
        
        for y in range(config.DISPLAY_HEIGHT):
            for x in range(config.DISPLAY_WIDTH):
                color = self.back_buffer[y][x]
                self.matrix.SetPixel(x, y, color[0], color[1], color[2])
        
        if config.DEBUG_MODE:
            print(f"Full update: {config.DISPLAY_WIDTH * config.DISPLAY_HEIGHT} pixels updated")
    
    def show_flight_info(self, flight_data: Dict[str, Any]):
        """
        Display flight information on the LED matrix using double buffering.
        New layout:
        - Line 1: Aircraft type (purple), with Canadian flag if Canadair aircraft
        - Line 2: Callsign (orange) 
        - Line 3: Route (light blue), with Canadian flag if Canadian origin
        
        Args:
            flight_data: Flight data dictionary
        """
        # Always initialize debug display for testing
        
        # Clear the back buffer
        self._clear_buffer()
        
        # Extract flight information
        callsign = flight_data.get("callsign", "Unknown")
        route = flight_data.get("route", "")
        aircraft_type = flight_data.get("aircraft_type", "")
        origin_code = flight_data.get("origin", "")
        
        # Check if aircraft is Canadian (Canadair RJ series)
        is_canadian_aircraft = aircraft_type and "Canadair" in aircraft_type
        
        # Define colors
        orange_color = (255, 165, 0)      # Orange for callsign
        light_blue_color = (173, 216, 230)  # Light blue for route
        purple_color = (128, 0, 128)      # Purple for aircraft type
        
        # Display flight info with new layout
        try:
            # Line 1: Aircraft type with Canadian flag if Canadair (y=2, centered horizontally)
            if aircraft_type:
                if is_canadian_aircraft:
                    # Calculate spacing for flag + aircraft type
                    flag_width = 13  # Canada flag is 13 pixels wide
                    flag_spacing = 2  # Space between flag and text
                    aircraft_type_width = len(aircraft_type) * 6  # 6 pixels per character
                    total_width = flag_width + flag_spacing + aircraft_type_width
                    
                    # Center the entire combination
                    start_x = (config.DISPLAY_WIDTH - total_width) // 2
                    
                    # Draw Canadian flag
                    self._draw_canada_flag(start_x, 2)
                    
                    # Draw aircraft type after flag
                    aircraft_x = start_x + flag_width + flag_spacing
                    self._draw_text_to_buffer(aircraft_type, aircraft_x, 2, purple_color)
                else:
                    # Normal aircraft type display without flag
                    aircraft_type_width = len(aircraft_type) * 6  # 6 pixels per character
                    aircraft_x = (config.DISPLAY_WIDTH - aircraft_type_width) // 2
                    self._draw_text_to_buffer(aircraft_type, aircraft_x, 2, purple_color)
            
            # Line 2: Callsign (y=12, centered horizontally)
            callsign_width = len(callsign) * 6  # 6 pixels per character
            callsign_x = (config.DISPLAY_WIDTH - callsign_width) // 2
            self._draw_text_to_buffer(callsign, callsign_x, 12, orange_color)
            
            # Line 3: Route (y=22, centered horizontally)
            # Check if origin is Canadian to show flag
            is_canadian_origin = origin_code in CANADIAN_AIRPORTS
            
            if is_canadian_origin:
                # Calculate spacing for flag + route
                flag_width = 13  # Canada flag is 13 pixels wide
                flag_spacing = 2  # Space between flag and text
                route_width = len(route) * 6  # 6 pixels per character
                total_width = flag_width + flag_spacing + route_width
                
                # Center the entire combination
                start_x = (config.DISPLAY_WIDTH - total_width) // 2
                
                # Draw Canadian flag
                self._draw_canada_flag(start_x, 22)
                
                # Draw route text after flag
                route_x = start_x + flag_width + flag_spacing
                self._draw_text_to_buffer(route, route_x, 22, light_blue_color)
            else:
                # Normal route display without flag
                route_width = len(route) * 6  # 6 pixels per character
                route_x = (config.DISPLAY_WIDTH - route_width) // 2
                self._draw_text_to_buffer(route, route_x, 22, light_blue_color)
            
            # Swap buffers to display the new content
            self._swap_buffers()
            
            
            if config.DEBUG_MODE:
                print(f"Displayed flight: {callsign} ({aircraft_type}) - {route}")
                
        except Exception as e:
            print(f"Error displaying flight info: {e}")
    
    def show_weather_info(self, weather_data: Dict[str, Any]):
        """
        Display weather and runway information with full-screen layout using double buffering.
        
        Args:
            weather_data: Weather data dictionary
        """
        # Always initialize debug display for testing
        
        # Clear the back buffer
        self._clear_buffer()
        
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
            self._draw_text_to_buffer(line1_text, 1, 2, config.ROW_ONE_COLOR)
            
            # Bottom section: Weather icon (18x18) on left + temperature & wind on right
            # Draw weather icon starting at y=12 (lines 2&3 combined)
            weather_condition = self._parse_weather_condition(metar)
            self._draw_weather_icon_to_buffer(weather_condition, 1, 12)
            
            # Draw temperature and wind on same line to the right of the icon
            temperature = self._extract_temperature_from_metar(metar)
            wind_info = self._extract_wind_from_metar(metar)
            
            # Combine temperature and wind on same line
            temp_text = temperature if temperature else "Temp: N/A"
            if wind_info:
                combined_text = f"{temp_text} {wind_info}"
            else:
                combined_text = temp_text
            
            self._draw_text_to_buffer(combined_text, 24, 16, config.ROW_THREE_COLOR)  # Start at x=24, with 2px more padding from icon
            
            # Swap buffers to display the new content
            self._swap_buffers()
            
            
            if config.DEBUG_MODE:
                print(f"Displayed weather: ARR={arrivals}, DEP={departures}, Temp={temperature if temperature else 'N/A'}")
                
        except Exception as e:
            print(f"Error displaying weather info: {e}")
    
    def show_no_flights_message(self, message_data: Dict[str, Any]):
        """Display message when no flights detected using double buffering."""
        # Always initialize debug display for testing
        
        # Clear the back buffer
        self._clear_buffer()
        
        try:
            # Available space: 128x32 (full display)
            # Text positions with proper spacing
            
            # Display "no flights" message with full screen space
            self._draw_text_to_buffer("No Approach", 1, 2, config.ROW_ONE_COLOR)
            self._draw_text_to_buffer("Traffic", 1, 12, config.ROW_TWO_COLOR)
            self._draw_text_to_buffer("Detected", 1, 22, config.ROW_THREE_COLOR)
            
            # Swap buffers to display the new content
            self._swap_buffers()
            
            
            if config.DEBUG_MODE:
                print("Displayed: No Approach Traffic Detected")
                
        except Exception as e:
            print(f"Error displaying no flights message: {e}")
    
    def show_plane_celebration(self, flight_data: Dict[str, Any]):
        """
        Display the full plane detection celebration sequence:
        1. Flash "Incoming Plane" text twice (amber)
        2. Animate purple plane from right to left
        3. Show flight information
        """
        try:
            # Step 1: Flash "Incoming Plane" text twice
            self._flash_incoming_plane_text()
            
            # Step 2: Animate purple plane
            self._animate_plane_crossing()
            
            # Step 3: Show flight information
            self.show_flight_info(flight_data)
            
        except Exception as e:
            print(f"Error in plane celebration: {e}")
    
    def _flash_incoming_plane_text(self):
        """Flash amber 'Incoming Plane' text twice with 1 second intervals."""
        amber_color = (255, 191, 0)  # Amber color
        
        for flash_count in range(2):
            # Clear and show text
            self._clear_buffer()
            
            # Center "Incoming Plane" text on display
            text = "Incoming Plane"
            text_width = len(text) * 6  # 6 pixels per character
            center_x = (config.DISPLAY_WIDTH - text_width) // 2
            center_y = (config.DISPLAY_HEIGHT - 8) // 2  # 8 pixels font height
            
            self._draw_text_to_buffer(text, center_x, center_y, amber_color)
            self._swap_buffers()
            
            # Show for 1 second
            time.sleep(1.0)
            
            # Clear display (black screen)
            self._clear_buffer()
            self._swap_buffers()
            
            # Pause for 1 second
            time.sleep(1.0)
    
    def _animate_plane_crossing(self):
        """Animate purple plane moving from right to left across center row."""
        plane_color = (128, 0, 128)  # Purple color
        center_y = config.DISPLAY_HEIGHT // 2  # Center row
        
        # 10x10 plane pattern designed by user
        plane_pattern = [
            "          ",
            "      PP  ",
            "    PPP   ",
            "  PPP   PP",
            "PPPPPPPPPP",
            "PPPPPPPPPP",
            "  PPP   PP",
            "    PPP   ",
            "      PP  ",
            "          "
        ]
        
        # Start from right edge, move to left edge
        start_x = config.DISPLAY_WIDTH
        end_x = -10  # Plane width (now 10 pixels wide)
        
        for x in range(start_x, end_x, -1):
            # Clear buffer
            self._clear_buffer()
            
            # Draw plane at current position (centered vertically)
            self._draw_plane_to_buffer(plane_pattern, x, center_y - 5, plane_color)
            
            # Update display
            self._swap_buffers()
            
            # Back to fast animation speed (0.1ms per tick)
            time.sleep(0.0001)  # 0.1 milliseconds
    
    def _draw_plane_to_buffer(self, pattern: list, x: int, y: int, color: tuple):
        """Draw a plane pattern to the back buffer."""
        for row, line in enumerate(pattern):
            for col, char in enumerate(line):
                if char == 'P':
                    pixel_x = x + col
                    pixel_y = y + row
                    if 0 <= pixel_x < config.DISPLAY_WIDTH and 0 <= pixel_y < config.DISPLAY_HEIGHT:
                        self._set_pixel_buffer(pixel_x, pixel_y, color)
    
    def _draw_static_plane_icon(self, x: int, y: int):
        """Draw the static plane icon used in flight info display."""
        plane_color = (128, 0, 128)  # Purple color
        
        # Same 10x10 plane pattern as animation
        plane_pattern = [
            "          ",
            "      PP  ",
            "    PPP   ",
            "  PPP   PP",
            "PPPPPPPPPP",
            "PPPPPPPPPP",
            "  PPP   PP",
            "    PPP   ",
            "      PP  ",
            "          "
        ]
        
        self._draw_plane_to_buffer(plane_pattern, x, y, plane_color)
    
    def clear_display(self):
        """Clear the LED matrix display using double buffering."""
        self._clear_buffer()
        self._swap_buffers()
    
    
    
    def _draw_text(self, text: str, x: int, y: int, color: tuple):
        """
        Draw text on the LED matrix using simple pixel patterns (legacy method).
        
        Args:
            text: Text to draw
            x: X position
            y: Y position
            color: RGB color tuple
        """
        # This is now a wrapper that calls the buffer-based method
        self._draw_text_to_buffer(text, x, y, color)
        
    def _draw_text_to_buffer(self, text: str, x: int, y: int, color: tuple):
        """
        Draw text to the back buffer using simple pixel patterns.
        
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
        
        # Calculate text bounding box for dirty region tracking
        text_width = len(text) * 6  # Each character is 6 pixels wide (5 + 1 space)
        text_height = 8  # Font height
        self._add_dirty_region(x, y, text_width, text_height)
        
        char_x = x
        for char in text.upper():
            if char in patterns:
                pattern = patterns[char]
                for row in range(8):  # 8 rows for new font
                    for col in range(5):  # 5 columns for new font
                        if pattern[row] & (1 << (4-col)):  # Check from bit 4 to 0
                            self._set_pixel_buffer(char_x + col, y + row, color)
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
        """Draw emoji-like weather icons on the LED matrix (legacy method)."""
        # This is now a wrapper that calls the buffer-based method
        self._draw_weather_icon_to_buffer(condition, x, y)
        
    def _draw_weather_icon_to_buffer(self, condition: str, x: int, y: int):
        """Draw emoji-like weather icons to the back buffer."""
        
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
        
        # Add dirty region for the entire icon
        self._add_dirty_region(x, y, 18, 18)
        
        for row, line in enumerate(icon):
            for col, char in enumerate(line):
                if char in colors and colors[char]:
                    color = colors[char]
                    pixel_x = x + col
                    pixel_y = y + row
                    
                    # Make sure we don't go outside display bounds
                    if pixel_x < config.DISPLAY_WIDTH and pixel_y < config.DISPLAY_HEIGHT:
                        self._set_pixel_buffer(pixel_x, pixel_y, color)

    def set_pixel(self, x: int, y: int, color: tuple):
        """Set a single pixel (public API for external use)."""
        self._set_pixel_buffer(x, y, color)
        
    def get_pixel(self, x: int, y: int) -> tuple:
        """Get the color of a pixel from the front buffer."""
        if 0 <= x < config.DISPLAY_WIDTH and 0 <= y < config.DISPLAY_HEIGHT:
            return self.front_buffer[y][x]
        return (0, 0, 0)
    
    def update_region(self, x: int, y: int, width: int, height: int):
        """Force update of a specific region on the next buffer swap."""
        self._add_dirty_region(x, y, width, height)
    
    def get_dirty_pixel_count(self) -> int:
        """Get the number of pixels that need updating."""
        return len(self.dirty_pixels)
    
    def is_hardware_ready(self) -> bool:
        """Check if hardware is ready for display operations."""
        return self.hardware_ready
    
    def get_display_size(self) -> tuple:
        """Get the display dimensions as (width, height)."""
        return (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: tuple):
        """Draw a line between two points."""
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            self._set_pixel_buffer(x, y, color)
            
            if x == x2 and y == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def draw_rectangle(self, x: int, y: int, width: int, height: int, color: tuple, filled: bool = False):
        """Draw a rectangle."""
        if filled:
            for dy in range(height):
                for dx in range(width):
                    self._set_pixel_buffer(x + dx, y + dy, color)
        else:
            # Draw rectangle outline
            for dx in range(width):
                self._set_pixel_buffer(x + dx, y, color)  # Top
                self._set_pixel_buffer(x + dx, y + height - 1, color)  # Bottom
            for dy in range(height):
                self._set_pixel_buffer(x, y + dy, color)  # Left
                self._set_pixel_buffer(x + width - 1, y + dy, color)  # Right
        
        self._add_dirty_region(x, y, width, height)
    
    def _draw_canada_flag(self, x: int, y: int):
        """Draw a small Canada flag icon (13x8 pixels)."""
        # 13x8 pixel Canada flag pattern
        # R = Red, W = White, . = transparent
        flag_pattern = [
            "RRR.......RRR",  # Row 0
            "RRR...R...RRR",  # Row 1 - start of maple leaf
            "RRR.R.R.R.RRR",  # Row 2 - maple leaf
            "RRR.RRRRR.RRR",  # Row 3 - maple leaf center
            "RRR..RRR..RRR",  # Row 4 - maple leaf
            "RRR.R.R.R.RRR",  # Row 5 - maple leaf stem
            "RRR...R...RRR",  # Row 6 - maple leaf stem
            "RRR.......RRR",  # Row 7
        ]
        
        # Color mapping
        colors = {
            'R': (255, 0, 0),      # Red
            'W': (255, 255, 255),  # White
            '.': None              # Transparent (don't draw)
        }
        
        # Add dirty region for the entire flag
        self._add_dirty_region(x, y, 13, 8)
        
        for row, line in enumerate(flag_pattern):
            for col, char in enumerate(line):
                if char == 'R':
                    # Draw red pixels
                    pixel_x = x + col
                    pixel_y = y + row
                    if pixel_x < config.DISPLAY_WIDTH and pixel_y < config.DISPLAY_HEIGHT:
                        self._set_pixel_buffer(pixel_x, pixel_y, colors['R'])
                elif char == 'W':
                    # Draw white pixels
                    pixel_x = x + col
                    pixel_y = y + row
                    if pixel_x < config.DISPLAY_WIDTH and pixel_y < config.DISPLAY_HEIGHT:
                        self._set_pixel_buffer(pixel_x, pixel_y, colors['W'])

# Global instance for easy access
display_controller = DisplayController()