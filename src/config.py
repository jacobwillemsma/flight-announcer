#!/usr/bin/env python3
"""
Flight Announcer Configuration
Configuration for the LGA flight monitoring LED matrix display.
"""

try:
    from env_loader import get_env_var, get_bool_env, get_cached_env
except ImportError:
    def get_env_var(key, default=None, env_vars=None):
        import os
        return os.environ.get(key, default)
    
    def get_bool_env(key, default=False, env_vars=None):
        import os
        value = os.environ.get(key, str(default).lower())
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_cached_env():
        return {}

# Load environment variables once
try:
    _env_vars = get_cached_env()
except:
    _env_vars = {}

# LED Matrix Configuration (from working test_matrix.py)
MATRIX_ROWS = 32
MATRIX_COLS = 64
MATRIX_CHAIN_LENGTH = 2
MATRIX_PARALLEL = 1
MATRIX_HARDWARE_MAPPING = 'adafruit-hat'

# Polling Intervals (seconds)
FLIGHT_POLL_INTERVAL = 30      # How often to check for flights
WEATHER_REFRESH_INTERVAL = 600 # How often to refresh weather (10 minutes)
SLEEP_WHEN_INACTIVE = 60       # Sleep time when runway not active

# LGA Approach Corridor Detection Box
# Updated coordinates for improved detection coverage
RWY04_BOUNDS_BOX = "-73.995667,40.648346,-73.870869,40.741527"

# Flight Filtering
MAX_APPROACH_ALTITUDE = 5000  # Only show flights below this altitude (approach traffic)

# Colors (RGB values for rgbmatrix)
ROW_ONE_COLOR = (192, 192, 192)    # Silver
ROW_TWO_COLOR = (192, 192, 192)    # Silver
ROW_THREE_COLOR = (192, 192, 192)  # Silver
PLANE_COLOR = (75, 0, 130)         # Indigo

# Animation and Timing
PAUSE_BETWEEN_LABEL_SCROLLING = 3  # Seconds between scrolling labels
PLANE_SPEED = 0.08                 # Speed of plane animation (pause per pixel)
TEXT_SPEED = 0.08                  # Speed of text scrolling

# FlightRadar24 API Configuration
FLIGHT_SEARCH_TAIL = "&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1&limit=1"

# Request Headers (for FlightRadar24 API)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "cache-control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
    "accept": "application/json"
}

# Display Layout
DISPLAY_WIDTH = MATRIX_COLS * MATRIX_CHAIN_LENGTH  # 128 pixels wide
DISPLAY_HEIGHT = MATRIX_ROWS  # 32 pixels tall

# Error Handling
MAX_CONNECTION_RETRIES = 3
CONNECTION_TIMEOUT = 10  # seconds

# Debug Settings (can be overridden by environment variables)
DEBUG_MODE = get_bool_env("DEBUG_MODE", False, _env_vars)
PRINT_MEMORY_INFO = get_bool_env("PRINT_MEMORY_INFO", False, _env_vars)