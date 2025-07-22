#!/usr/bin/env python3
"""
Flight Announcer Main Application
Displays flight information on LED matrix when planes are detected at LGA,
otherwise shows weather and METAR information.
"""

import time
import sys
import os
import signal
import threading
from typing import Dict, Any
from datetime import datetime

try:
    from flight_logic import flight_logic
    from display_controller import display_controller
    from stats_tracker import FlightStatsTracker
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the src/ directory")
    sys.exit(1)

# Initialize stats tracker
stats_tracker = None
if config.STATS_ENABLED:
    try:
        stats_tracker = FlightStatsTracker(config.STATS_DB_PATH)
    except Exception as e:
        print(f"Failed to initialize stats tracking: {e}")


class FlightAnnouncer:
    """Main application class for the Flight Announcer."""
    
    def __init__(self):
        self.running = True
        self.plane_detected = False
        self.last_weather_update = 0
        self.last_plane_check = 0
        self.current_plane_data = None
        
        # Use the module-level stats tracker instance
        self.stats_tracker = stats_tracker
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main application entry point with simplified timing loop."""
        print("=" * 60)
        print("Flight Announcer - LGA Approach Monitor")
        print("=" * 60)
        print(f"Display: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
        print(f"Weather refresh interval: {config.WEATHER_REFRESH_INTERVAL}s")
        print(f"Flight poll interval: {config.FLIGHT_POLL_INTERVAL}s")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        # Clear display on startup
        display_controller.clear_display()
        
        try:
            # Simple main loop
            while self.running:
                current_time = time.time()
                
                # Check for planes every 30 seconds
                if current_time - self.last_plane_check >= config.FLIGHT_POLL_INTERVAL:
                    self._check_for_planes()
                    self.last_plane_check = current_time
                
                # Update weather every 10 minutes
                if current_time - self.last_weather_update >= config.WEATHER_REFRESH_INTERVAL:
                    self._update_weather()
                    self.last_weather_update = current_time
                
                # Display logic
                if self.plane_detected and self.current_plane_data:
                    # Keep showing flight info while plane is detected
                    self._display_flight_data(self.current_plane_data)
                else:
                    # Default to weather display
                    self._display_weather()
                
                # Sleep for 1 second before next iteration
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self._cleanup()
    
    def _check_for_planes(self):
        """Check for planes in the approach corridor."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            flight_data = flight_logic.get_approaching_flights()
            
            if flight_data:
                if not self.plane_detected:
                    # New plane detected - show celebration
                    print(f"[{timestamp}] ✈️  FLIGHT DETECTED: {flight_data.get('callsign', 'Unknown')}")
                    self.plane_detected = True
                    self.current_plane_data = flight_data
                    self.current_plane_data["type"] = "flight"
                    display_controller.show_plane_celebration(flight_data)
                    
                    # Record flight stats
                    if self.stats_tracker:
                        try:
                            self.stats_tracker.record_flight(flight_data)
                            print(f"[{timestamp}] 📊  Flight recorded to stats")
                        except Exception as e:
                            print(f"[{timestamp}] ❌  Failed to record flight stats: {e}")
                else:
                    # Plane still detected - update data
                    print(f"[{timestamp}] ✈️  FLIGHT STILL DETECTED: {flight_data.get('callsign', 'Unknown')}")
                    self.current_plane_data = flight_data
                    self.current_plane_data["type"] = "flight"
            else:
                if self.plane_detected:
                    # Plane no longer detected
                    print(f"[{timestamp}] 🌤️  FLIGHT NO LONGER DETECTED")
                    self.plane_detected = False
                    self.current_plane_data = None
                else:
                    # No plane detected and none was detected before
                    print(f"[{timestamp}] 🔍  PLANE CHECK: No flights detected")
                    
        except Exception as e:
            print(f"[{timestamp}] ❌  Error checking for planes: {e}")
    
    def _update_weather(self):
        """Update weather data."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.weather_data = flight_logic.get_weather_display(force_refresh=True)
            arrivals = self.weather_data.get('arrivals_runway', 'Unknown')
            departures = self.weather_data.get('departures_runway', 'Unknown')
            metar = self.weather_data.get('metar', '')
            
            # Extract temperature and wind information
            temperature = display_controller._extract_temperature_from_metar(metar)
            wind_info = display_controller._extract_wind_from_metar(metar)
            
            # Build weather info string
            weather_info = f"ARR=RWY{arrivals}, DEP=RWY{departures}"
            if temperature:
                weather_info += f", {temperature}"
            if wind_info:
                weather_info += f", {wind_info}"
            
            print(f"[{timestamp}] 🌤️  Weather updated: {weather_info}")
        except Exception as e:
            print(f"[{timestamp}] ❌  Error updating weather: {e}")
    
    def _display_weather(self):
        """Display weather as the holding screen."""
        try:
            if not hasattr(self, 'weather_data') or not self.weather_data:
                self.weather_data = flight_logic.get_weather_display()
            
            if self.weather_data:
                display_controller.show_weather_info(self.weather_data)
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] ❌  Error displaying weather: {e}")
    
    
    def _display_flight_data(self, data: Dict[str, Any]):
        """Display flight information."""
        display_controller.show_flight_info(data)
    
    
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