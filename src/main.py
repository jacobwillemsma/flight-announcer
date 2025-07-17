#!/usr/bin/env python3
"""
Flight Announcer Main Application
Displays flight information on LED matrix when runway 04 is active at LGA,
otherwise shows weather and METAR information.
"""

import time
import sys
import signal
from typing import Dict, Any

try:
    from flight_logic import flight_logic
    from display_controller import display_controller
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the src/ directory")
    sys.exit(1)

class FlightAnnouncer:
    """Main application class for the Flight Announcer."""
    
    def __init__(self):
        self.running = True
        self.last_display_update = 0
        self.current_display_data = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main application loop."""
        print("=" * 60)
        print("Flight Announcer - LGA Runway 04 Monitor")
        print("=" * 60)
        print(f"Display: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
        print(f"Runway check interval: {config.RUNWAY_CHECK_INTERVAL}s")
        print(f"Weather refresh interval: {config.WEATHER_REFRESH_INTERVAL}s")
        print(f"Flight poll interval: {config.FLIGHT_POLL_INTERVAL}s")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        # Clear display on startup
        display_controller.clear_display()
        
        try:
            while self.running:
                self._update_display()
                time.sleep(config.FLIGHT_POLL_INTERVAL)
        
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self._cleanup()
    
    def _update_display(self):
        """Update the display based on current conditions."""
        try:
            # Get current display data
            display_data = flight_logic.get_display_data()
            
            if not display_data:
                if config.DEBUG_MODE:
                    print("No display data available")
                return
            
            # Check if we need to update the display
            if self._should_update_display(display_data):
                self._display_data(display_data)
                self.current_display_data = display_data
                self.last_display_update = time.time()
        
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def _should_update_display(self, new_data: Dict[str, Any]) -> bool:
        """Determine if display should be updated."""
        # Always update if no current data
        if not self.current_display_data:
            return True
        
        # Check if data type changed
        if new_data.get("type") != self.current_display_data.get("type"):
            return True
        
        # For flight data, update if different flight
        if new_data.get("type") == "flight":
            return (new_data.get("flight_id") != self.current_display_data.get("flight_id") or
                    new_data.get("callsign") != self.current_display_data.get("callsign"))
        
        # For weather data, update if runway changed or every 5 seconds for alternating text
        if new_data.get("type") == "weather":
            runway_changed = (new_data.get("arrivals_runway") != self.current_display_data.get("arrivals_runway") or
                            new_data.get("departures_runway") != self.current_display_data.get("departures_runway"))
            # Also update every 5 seconds to handle alternating text
            time_since_update = time.time() - self.last_display_update
            return runway_changed or time_since_update >= 5.0
        
        # For no_flights message, update if runway status changed
        if new_data.get("type") == "no_flights":
            return True  # Always update these messages
        
        return False
    
    def _display_data(self, data: Dict[str, Any]):
        """Display the appropriate data on the LED matrix."""
        data_type = data.get("type", "unknown")
        
        if data_type == "flight":
            self._display_flight_data(data)
        elif data_type == "weather":
            self._display_weather_data(data)
        elif data_type == "no_flights":
            self._display_no_flights_data(data)
        else:
            if config.DEBUG_MODE:
                print(f"Unknown data type: {data_type}")
    
    def _display_flight_data(self, data: Dict[str, Any]):
        """Display flight information."""
        callsign = data.get("callsign", "Unknown")
        aircraft = data.get("aircraft_type", "")
        altitude = data.get("altitude", 0)
        route = data.get("route", "")
        
        print(f"✈️  FLIGHT: {callsign} - {aircraft} at {altitude}ft - {route}")
        
        display_controller.show_flight_info(data)
    
    def _display_weather_data(self, data: Dict[str, Any]):
        """Display weather information."""
        arrivals = data.get("arrivals_runway", "Unknown")
        departures = data.get("departures_runway", "Unknown")
        metar = data.get("metar", "Weather unavailable")
        
        print(f"🌤️  WEATHER: ARR=RWY{arrivals}, DEP=RWY{departures}")
        if config.DEBUG_MODE:
            print(f"   METAR: {metar}")
        
        display_controller.show_weather_info(data)
    
    def _display_no_flights_data(self, data: Dict[str, Any]):
        """Display no flights message."""
        runway_status = data.get("runway_status", {})
        arrivals = runway_status.get("arrivals", "Unknown")
        
        print(f"🛬 RWY04 ACTIVE: No approach traffic (ARR=RWY{arrivals})")
        
        display_controller.show_no_flights_message(data)
    
    def _cleanup(self):
        """Clean up resources before exit."""
        print("\nCleaning up...")
        display_controller.clear_display()
        print("Flight Announcer stopped")

def main():
    """Main entry point."""
    app = FlightAnnouncer()
    app.run()

if __name__ == "__main__":
    main()