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
import sqlite3
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

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

class FlightStatsTracker:
    def __init__(self, db_path: str = "flight_stats.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS flights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    callsign TEXT,
                    aircraft_type TEXT,
                    origin TEXT,
                    airline TEXT,
                    timestamp DATETIME,
                    date TEXT,
                    is_helicopter BOOLEAN DEFAULT 0,
                    is_private_jet BOOLEAN DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_planes INTEGER DEFAULT 0,
                    helicopters INTEGER DEFAULT 0,
                    private_jets INTEGER DEFAULT 0,
                    origins_json TEXT,
                    airlines_json TEXT,
                    aircraft_types_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_flights_date ON flights(date)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_flights_timestamp ON flights(timestamp)
            """)
    
    def record_flight(self, flight_data: Dict[str, Any]):
        with self.lock:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            
            callsign = flight_data.get('callsign', '')
            aircraft_type = flight_data.get('aircraft_type', '')
            origin = flight_data.get('origin', '')
            airline = flight_data.get('airline', '')
            
            is_helicopter = self._is_helicopter(aircraft_type)
            is_private_jet = self._is_private_jet(callsign, aircraft_type)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO flights (callsign, aircraft_type, origin, airline, timestamp, date, is_helicopter, is_private_jet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (callsign, aircraft_type, origin, airline, now, today, is_helicopter, is_private_jet))
                
                self._update_daily_stats(conn, today, origin, airline, aircraft_type, is_helicopter, is_private_jet)
    
    def _is_helicopter(self, aircraft_type: str) -> bool:
        helicopter_types = ['H60', 'EC35', 'AS35', 'BK17', 'H500', 'R22', 'R44', 'R66', 'EC20', 'EC45']
        return aircraft_type.upper() in [h.upper() for h in helicopter_types]
    
    def _is_private_jet(self, callsign: str, aircraft_type: str) -> bool:
        if not callsign:
            return False
        
        private_prefixes = ['N', 'G-', 'C-', 'D-', 'F-', 'I-', 'PH-', 'OO-', 'HB-', 'LX-', 'VP-', 'M-']
        jet_types = ['GLF', 'CL60', 'C56X', 'C680', 'C700', 'CL30', 'FA50', 'H25B', 'LJ60', 'CRJ', 'EMB']
        
        has_private_prefix = any(callsign.upper().startswith(prefix.upper()) for prefix in private_prefixes)
        has_jet_type = any(jet_type.upper() in aircraft_type.upper() for jet_type in jet_types)
        
        return has_private_prefix or has_jet_type
    
    def _update_daily_stats(self, conn, date_str: str, origin: str, airline: str, aircraft_type: str, is_helicopter: bool, is_private_jet: bool):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date_str,))
        existing = cursor.fetchone()
        
        if existing:
            total_planes = existing[1] + 1
            helicopters = existing[2] + (1 if is_helicopter else 0)
            private_jets = existing[3] + (1 if is_private_jet else 0)
            origins = json.loads(existing[4] or '{}')
            airlines = json.loads(existing[5] or '{}')
            aircraft_types = json.loads(existing[6] or '{}')
        else:
            total_planes = 1
            helicopters = 1 if is_helicopter else 0
            private_jets = 1 if is_private_jet else 0
            origins = {}
            airlines = {}
            aircraft_types = {}
        
        if origin:
            origins[origin] = origins.get(origin, 0) + 1
        if airline:
            airlines[airline] = airlines.get(airline, 0) + 1
        if aircraft_type:
            aircraft_types[aircraft_type] = aircraft_types.get(aircraft_type, 0) + 1
        
        conn.execute("""
            INSERT OR REPLACE INTO daily_stats 
            (date, total_planes, helicopters, private_jets, origins_json, airlines_json, aircraft_types_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date_str, total_planes, helicopters, private_jets, 
              json.dumps(origins), json.dumps(airlines), json.dumps(aircraft_types)))

# Initialize stats tracker
stats_tracker = None
if config.STATS_ENABLED:
    try:
        stats_tracker = FlightStatsTracker(config.STATS_DB_PATH)
        print(f"Stats tracking enabled: {config.STATS_DB_PATH}")
    except Exception as e:
        print(f"Failed to initialize stats tracking: {e}")
        print("Continuing without stats tracking...")

if __name__ == "__main__":
    main()