#!/usr/bin/env python3
"""
Flight Announcer Main Application
Displays flight information on LED matrix when runway 04 is active at LGA,
otherwise shows weather and METAR information.
"""

import time
import sys
import signal
import threading
from typing import Dict, Any

try:
    from flight_logic import flight_logic
    from display_controller import display_controller
    import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the src/ directory")
    sys.exit(1)

class SharedDisplayState:
    """Thread-safe shared state for display data."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._current_data = None
        self._last_data_update = 0
        
    def update_data(self, data: Dict[str, Any]):
        """Update the shared display data."""
        with self._lock:
            self._current_data = data
            self._last_data_update = time.time()
    
    def get_data(self) -> Dict[str, Any]:
        """Get the current display data."""
        with self._lock:
            return self._current_data.copy() if self._current_data else None
    
    def get_last_update_time(self) -> float:
        """Get the timestamp of the last data update."""
        with self._lock:
            return self._last_data_update

class FlightAnnouncer:
    """Main application class for the Flight Announcer."""
    
    def __init__(self):
        self.running = True
        self.shared_state = SharedDisplayState()
        
        # Thread objects
        self.data_thread = None
        self.display_thread = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main application entry point."""
        print("=" * 60)
        print("Flight Announcer - LGA Runway 04 Monitor")
        print("=" * 60)
        print(f"Display: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
        print(f"Runway check interval: {config.RUNWAY_CHECK_INTERVAL}s")
        print(f"Weather refresh interval: {config.WEATHER_REFRESH_INTERVAL}s")
        print(f"Flight poll interval: {config.FLIGHT_POLL_INTERVAL}s")
        print(f"Display refresh: ~100ms (for scrolling/alternating text)")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        
        # Clear display on startup
        display_controller.clear_display()
        
        try:
            # Start data fetching thread
            self.data_thread = threading.Thread(target=self._data_loop, daemon=True)
            self.data_thread.start()
            
            # Start display thread
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            
            # Keep main thread alive
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self._cleanup()
    
    def _data_loop(self):
        """Background thread for data fetching (respects API intervals)."""
        while self.running:
            try:
                # Get current display data from flight logic
                display_data = flight_logic.get_display_data()
                
                if display_data:
                    # Update shared state
                    self.shared_state.update_data(display_data)
                    
                    if config.DEBUG_MODE:
                        data_type = display_data.get("type", "unknown")
                        print(f"Data thread: Updated {data_type} data")
                
                # Sleep according to data type - faster for flights, slower for weather
                current_data = self.shared_state.get_data()
                if current_data and current_data.get("type") == "flight":
                    time.sleep(config.FLIGHT_POLL_INTERVAL)
                else:
                    time.sleep(config.FLIGHT_POLL_INTERVAL)  # Use same interval for now
                    
            except Exception as e:
                print(f"Error in data loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _display_loop(self):
        """Fast display loop for visual updates (scrolling, alternating text)."""
        last_displayed_data = None
        last_data_update_time = 0
        last_alternating_check = 0
        
        while self.running:
            try:
                # Get current data from shared state
                current_data = self.shared_state.get_data()
                data_update_time = self.shared_state.get_last_update_time()
                current_time = time.time()
                
                needs_update = False
                
                if current_data:
                    # Update if new data arrived
                    if data_update_time > last_data_update_time:
                        needs_update = True
                        last_data_update_time = data_update_time
                        if config.DEBUG_MODE:
                            print("Display update: New data received")
                    
                    # Update if alternating text should change (only for weather)
                    elif (current_data.get("type") == "weather" and 
                          current_time - last_alternating_check >= 3.0):
                        needs_update = True
                        last_alternating_check = current_time
                        if config.DEBUG_MODE:
                            print("Display update: Alternating text timer")
                    
                    # Only redraw if something actually changed
                    if needs_update:
                        self._display_data(current_data)
                        last_displayed_data = current_data
                
                # Check every 100ms but only update when needed
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in display loop: {e}")
                time.sleep(1)  # Wait before retrying
    
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