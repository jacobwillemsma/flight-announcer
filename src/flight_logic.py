#!/usr/bin/env python3
"""
Flight Logic
Handles all flight data, runway detection, and caching logic.
"""

import time
import json
import re
from typing import Dict, Optional, Any, List
import requests

try:
    from lga_client import get_current_metar, get_active_runways
    import config
except ImportError:
    try:
        from .lga_client import get_current_metar, get_active_runways
        from . import config
    except ImportError:
        print("Error: Could not import required modules")
        exit(1)

class FlightLogic:
    """Handles flight data and runway logic with simplified timing."""
    
    def __init__(self):
        # FlightAware AeroAPI endpoints
        self.flight_search_url = f"{config.FLIGHTAWARE_BASE_URL}/flights/search"
        
        # Convert bounds box to FlightAware format
        # Config has: "lat_max,lat_min,lon_min,lon_max" format
        # FlightAware needs: individual lat/lon parameters
        bounds = config.RWY04_BOUNDS_BOX.split(",")
        self.search_bounds = {
            "lat_min": float(bounds[1]),  # SW latitude
            "lat_max": float(bounds[0]),  # NE latitude  
            "lon_min": float(bounds[2]),  # SW longitude
            "lon_max": float(bounds[3])   # NE longitude
        }
    
    def check_runway_status(self) -> Dict[str, Any]:
        """
        Check current runway status.
        
        Returns:
            dict: {"runway_04_active": bool, "arrivals": str, "departures": str, "last_updated": float}
        """
        current_time = time.time()
        
        # Fetch fresh runway data
        try:
            runways = get_active_runways()
            arrivals = runways.get("arrivals")
            departures = runways.get("departures")
            
            # Check if runway 04 is active for arrivals
            runway_04_active = False
            if arrivals:
                # Remove L/C/R suffixes and check if it's runway 04
                runway_num = re.sub(r'[LCR]$', '', arrivals)
                runway_04_active = runway_num in ['04', '4']
            
            return {
                "runway_04_active": runway_04_active,
                "arrivals": arrivals,
                "departures": departures,
                "last_updated": current_time
            }
            
        except Exception as e:
            print(f"Error checking runway status: {e}")
            return {
                "runway_04_active": False,
                "arrivals": None,
                "departures": None,
                "last_updated": current_time
            }
    
    def get_approaching_flights(self) -> Optional[Dict[str, Any]]:
        """
        Get flight data for approach corridor using FlightAware AeroAPI.
        
        Returns:
            dict: Flight data or None if no flights found
        """
        try:
            # FlightAware AeroAPI search parameters
            params = {
                "query": f"-aboveAltitude 0 -belowAltitude {config.MAX_APPROACH_ALTITUDE} -latlong {self.search_bounds['lat_min']},{self.search_bounds['lon_min']},{self.search_bounds['lat_max']},{self.search_bounds['lon_max']}",
                "max_pages": 1
            }
            
            response = requests.get(
                url=self.flight_search_url,
                params=params,
                headers=config.get_flightaware_headers(),
                timeout=config.CONNECTION_TIMEOUT
            )
            
            if response.status_code != 200:
                print(f"FlightAware API returned status {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            
            # Check if we have flights in the response
            if 'flights' in data and len(data['flights']) > 0:
                # Get the first flight (closest/most relevant)
                flight_info = data['flights'][0]
                
                # Check if flight has valid altitude data
                if 'last_position' in flight_info and flight_info['last_position']:
                    altitude = flight_info['last_position'].get('altitude', 0)
                    if altitude and altitude < config.MAX_APPROACH_ALTITUDE:
                        # Parse flight information
                        flight_data = self._parse_flightaware_data(flight_info)
                        if flight_data:
                            return flight_data
            
            # No valid flights found
            return None
            
        except Exception as e:
            print(f"Error fetching flights from FlightAware: {e}")
            return None
    
    def _parse_flightaware_data(self, flight_info: Dict) -> Optional[Dict[str, Any]]:
        """Parse FlightAware API response into structured format."""
        try:
            # Extract flight details from FlightAware format
            ident = flight_info.get('ident', 'Unknown')
            aircraft_type = flight_info.get('aircraft_type', 'Unknown')
            
            # Get altitude from last position
            altitude = 0
            if 'last_position' in flight_info and flight_info['last_position']:
                altitude = flight_info['last_position'].get('altitude', 0)
            
            # Get origin and destination
            origin = flight_info.get('origin', {}).get('code_iata', 'Unknown')
            destination = flight_info.get('destination', {}).get('code_iata', 'Unknown')
            
            # If IATA codes not available, try ICAO codes
            if origin == 'Unknown' or origin is None:
                origin = flight_info.get('origin', {}).get('code_icao', 'Unknown')
            if destination == 'Unknown' or destination is None:
                destination = flight_info.get('destination', {}).get('code_icao', 'Unknown')
            
            return {
                "flight_id": flight_info.get('fa_flight_id', 'Unknown'),
                "callsign": ident,
                "aircraft_type": aircraft_type,
                "altitude": altitude,
                "speed": flight_info.get('last_position', {}).get('groundspeed', 0) if flight_info.get('last_position') else 0,
                "origin": origin,
                "destination": destination,
                "route": f"{origin} → {destination}"
            }
            
        except Exception as e:
            print(f"Error parsing FlightAware data: {e}")
            return None
    
    def get_weather_display(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get weather and runway information for display.
        
        Returns:
            dict: Weather display data
        """
        current_time = time.time()
        
        # Fetch fresh weather data
        try:
            metar = get_current_metar()
            runway_status = self.check_runway_status()
            
            return {
                "type": "weather",
                "metar": metar,
                "arrivals_runway": runway_status.get("arrivals", "Unknown"),
                "departures_runway": runway_status.get("departures", "Unknown"),
                "last_updated": current_time
            }
            
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return {
                "type": "weather",
                "metar": "Weather unavailable",
                "arrivals_runway": "Unknown",
                "departures_runway": "Unknown",
                "last_updated": current_time
            }
    
    
    def check_for_planes_now(self) -> Dict[str, Any]:
        """Easy testing function to check for planes in the approach corridor right now."""
        print("\n=== PLANE CHECK (DEBUG) ===")
        
        # Check for flights
        flight_data = self.get_approaching_flights()
        
        if flight_data:
            print(f"✈️  PLANE DETECTED:")
            print(f"   Callsign: {flight_data.get('callsign', 'Unknown')}")
            print(f"   Aircraft: {flight_data.get('aircraft_type', 'Unknown')}")
            print(f"   Altitude: {flight_data.get('altitude', 0)} feet")
            print(f"   Route: {flight_data.get('route', 'Unknown')}")
            print(f"   Flight ID: {flight_data.get('flight_id', 'Unknown')}")
            return flight_data
        else:
            print("🌤️  NO PLANES DETECTED in approach corridor")
            
            # Also check runway status for context
            runway_status = self.check_runway_status()
            print(f"   Current runways: ARR={runway_status.get('arrivals', 'Unknown')}, DEP={runway_status.get('departures', 'Unknown')}")
            return None
        
        print("=========================\n")

# Global instance for easy access
flight_logic = FlightLogic()

# Easy testing function
def check_for_planes():
    """Quick function to check for planes - for testing/debugging."""
    return flight_logic.check_for_planes_now()