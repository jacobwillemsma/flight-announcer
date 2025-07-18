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
FLIGHT_POLL_INTERVAL = 20      # How often to check for flights
RUNWAY_CHECK_INTERVAL = 900    # How often to check ATIS for runway changes (15 minutes)
WEATHER_REFRESH_INTERVAL = 300 # How often to refresh weather when not RWY04 (5 minutes)
SLEEP_WHEN_INACTIVE = 60       # Sleep time when runway not active

# LGA Runway 04 Approach Corridor (the only one we can see)
# NE: 40°44'29.9"N 73°54'24.7"W, SW: 40°42'04.7"N 73°56'34.2"W (1-mile buffer)
RWY04_BOUNDS_BOX = "40.756132,40.686813,-73.961956,-73.887739"

# Flight Filtering
MAX_APPROACH_ALTITUDE = 5000  # Only show flights below this altitude (approach traffic)

# Colors (RGB values for rgbmatrix)
ROW_ONE_COLOR = (100, 150, 255)    # Light Blue
ROW_TWO_COLOR = (100, 150, 255)    # Light Blue
ROW_THREE_COLOR = (100, 150, 255)  # Light Blue
PLANE_COLOR = (75, 0, 130)         # Indigo

# Animation and Timing
PAUSE_BETWEEN_LABEL_SCROLLING = 3  # Seconds between scrolling labels
PLANE_SPEED = 0.08                 # Speed of plane animation (pause per pixel)
TEXT_SPEED = 0.08                  # Speed of text scrolling

# FlightAware AeroAPI Configuration
FLIGHTAWARE_API_KEY = get_env_var("FLIGHTAWARE_API_KEY", None, _env_vars)
FLIGHTAWARE_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

# Validate API key is available
if not FLIGHTAWARE_API_KEY:
    print("Warning: FLIGHTAWARE_API_KEY environment variable not set!")
    print("Set it with: export FLIGHTAWARE_API_KEY='your_api_key_here'")
    FLIGHTAWARE_API_KEY = ""  # Fallback to empty string

# Request Headers (for FlightAware AeroAPI)
def get_flightaware_headers():
    """Get headers with API key, checking if key is available."""
    if not FLIGHTAWARE_API_KEY:
        raise ValueError("FlightAware API key not configured. Set FLIGHTAWARE_API_KEY environment variable.")
    
    return {
        "x-apikey": FLIGHTAWARE_API_KEY,
        "Accept": "application/json; charset=UTF-8"
    }

# Keep the old format for backwards compatibility
REQUEST_HEADERS = get_flightaware_headers() if FLIGHTAWARE_API_KEY else {}

# Display Layout
DISPLAY_WIDTH = MATRIX_COLS * MATRIX_CHAIN_LENGTH  # 128 pixels wide
DISPLAY_HEIGHT = MATRIX_ROWS  # 32 pixels tall

# Error Handling
MAX_CONNECTION_RETRIES = 3
CONNECTION_TIMEOUT = 10  # seconds

# Debug Settings (can be overridden by environment variables)
DEBUG_MODE = get_bool_env("DEBUG_MODE", False, _env_vars)
PRINT_MEMORY_INFO = get_bool_env("PRINT_MEMORY_INFO", False, _env_vars)