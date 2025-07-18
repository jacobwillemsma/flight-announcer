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

# Airline code to name mapping
AIRLINE_CODES = {
    "EDV": "Endeavor",
    "DL": "Delta",
    "DAL": "Delta", 
    "AA": "American",
    "AAL": "American",
    "UA": "United",
    "UAL": "United",
    "JBU": "JetBlue",
    "B6": "JetBlue",
    "WN": "Southwest",
    "SWA": "Southwest",
    "AS": "Alaska",
    "ASA": "Alaska",
    "NK": "Spirit",
    "NKS": "Spirit",
    "F9": "Frontier",
    "FFT": "Frontier",
    "G4": "Allegiant",
    "AAY": "Allegiant",
    "HA": "Hawaiian",
    "HAL": "Hawaiian",
    "AC": "Air Canada",
    "ACA": "Air Canada",
    "WS": "WestJet",
    "WJA": "WestJet",
    "RPA": "Republic"
}

# Airport code to name mapping
AIRPORT_CODES = {
    "PWM": "Portland",
    "BGR": "Bangor",
    "BUF": "Buffalo",
    "BOS": "Boston",
    "PVD": "Providence", 
    "BDL": "Hartford",
    "DCA": "Washington",
    "IAD": "Dulles",
    "BWI": "Baltimore",
    "PHL": "Philadelphia",
    "EWR": "Newark",
    "ORD": "Chicago",
    "MDW": "Midway",
    "DTW": "Detroit",
    "MSP": "Minneapolis",
    "ATL": "Atlanta",
    "MIA": "Miami",
    "FLL": "Fort Lauderdale",
    "TPA": "Tampa",
    "MCI": "Kansas City",
    "MCO": "Orlando",
    "CLT": "Charlotte",
    "RDU": "Raleigh",
    "DEN": "Denver",
    "PHX": "Phoenix",
    "LAS": "Las Vegas",
    "LAX": "Los Angeles",
    "SAN": "San Diego",
    "SFO": "San Francisco",
    "OAK": "Oakland",
    "SJC": "San Jose",
    "SEA": "Seattle",
    "PDX": "Portland OR",
    "DAL": "Dallas",
    "ORF": "Norfolk",
    "BNA": "Nashville",
    "RSW": "Fort Myers",
    "MYR": "Myrtle Beach",
    "CVG": "Cincinnati",
    "ALB": "Albany",
    "TYS": "Knoxville",
    "GRR": "Grand Rapids",
    "DFW": "Dallas",
    "SDF": "Louisville",
    "CLE": "Cleveland",
    "STL": "St. Louis",
    "ACK": "Nantucket",
    "SAV": "Savannah",
    "XNA": "NW Arkansas",
    "YYZ": "Toronto",
    "YUL": "Montreal",
    "YVR": "Vancouver"
}

# Canadian airports
CANADIAN_AIRPORTS = {"YYZ", "YUL", "YVR"}

def extract_airline_code(callsign: str) -> Optional[str]:
    """Extract airline code from callsign (e.g., 'EDV5361' -> 'EDV')."""
    if not callsign:
        return None
    
    # Most airline callsigns start with 2-3 letter codes
    # Try 3-letter codes first, then 2-letter codes
    for length in [3, 2]:
        if len(callsign) > length:
            code = callsign[:length]
            if code in AIRLINE_CODES:
                return code
    
    return None

def get_airline_name(callsign: str) -> str:
    """Get airline name from callsign, or return original if not found."""
    airline_code = extract_airline_code(callsign)
    if airline_code and airline_code in AIRLINE_CODES:
        # Return airline name + flight number
        flight_number = callsign[len(airline_code):]
        return f"{AIRLINE_CODES[airline_code]} {flight_number}"
    return callsign

# Aircraft type code to name mapping
AIRCRAFT_TYPES = {
    "BCS3": "Airbus A220-300",
    "BCS1": "Airbus A220-100",
    "A319": "Airbus A319",
    "A320": "Airbus A320",
    "A321": "Airbus A321",
    "A330": "Airbus A330",
    "A340": "Airbus A340",
    "A350": "Airbus A350",
    "A380": "Airbus A380",
    "B737": "Boeing 737",
    "B738": "Boeing 737-800",
    "B739": "Boeing 737-900",
    "B38M": "Boeing 737 MAX 8",
    "B39M": "Boeing 737 MAX 9",
    "B752": "Boeing 757-200",
    "B753": "Boeing 757-300",
    "B762": "Boeing 767-200",
    "B763": "Boeing 767-300",
    "B764": "Boeing 767-400",
    "B772": "Boeing 777-200",
    "B773": "Boeing 777-300",
    "B77W": "Boeing 777-300ER",
    "B787": "Boeing 787",
    "B788": "Boeing 787-8",
    "B789": "Boeing 787-9",
    "CRJ2": "Canadair CRJ-200",
    "CRJ7": "Canadair CRJ-700",
    "CRJ9": "Canadair CRJ-900",
    "E170": "Embraer E170",
    "E175": "Embraer E175",
    "E75S": "Embraer E175",
    "E75L": "Embraer E175",
    "E190": "Embraer E190",
    "E195": "Embraer E195",
    "DH8A": "Dash 8-100",
    "DH8B": "Dash 8-200",
    "DH8C": "Dash 8-300",
    "DH8D": "Dash 8-400"
}

def get_airport_name(airport_code: str) -> str:
    """Get airport name from code, or return original if not found."""
    if airport_code in AIRPORT_CODES:
        return AIRPORT_CODES[airport_code]
    return airport_code

# Private jet aircraft codes
PRIVATE_JET_CODES = {
    "C25A": "Cessna Citation CJ2",
    "C25B": "Cessna Citation CJ3",
    "C25C": "Cessna Citation CJ4",
    "C510": "Cessna Citation Mustang",
    "C525": "Cessna Citation M2",
    "C550": "Cessna Citation II",
    "C560": "Cessna Citation V",
    "C680": "Cessna Citation Sov",
    "C750": "Cessna Citation X",
    "CL30": "Bombardier CL300",
    "CL35": "Bombardier CL350",
    "CL60": "Bombardier CL600",
    "CL65": "Bombardier CL650",
    "BD10": "Bombardier G6000",
    "GL5T": "Bombardier G5000",
    "GLEX": "Bombardier Global",
    "GLF4": "Gulfstream IV",
    "GLF5": "Gulfstream V",
    "GLF6": "Gulfstream G6",
    "G280": "Gulfstream G280",
    "G450": "Gulfstream G450",
    "G550": "Gulfstream G550",
    "G650": "Gulfstream G650",
    "HDJT": "Honda Jet",
    "E50P": "Embraer Phenom 100",
    "E55P": "Embraer Phenom 300",
    "LJ35": "Learjet 35",
    "LJ45": "Learjet 45",
    "LJ60": "Learjet 60",
    "LJ75": "Learjet 75",
    "BE20": "Beechcraft King Air 200",
    "BE40": "Beechcraft Premier I",
    "BE9L": "Beechcraft King Air 90",
    "TBM7": "TBM 700",
    "TBM8": "TBM 800",
    "TBM9": "TBM 900",
    "PC12": "Pilatus PC-12",
    "DA40": "Diamond DA40",
    "DA62": "Diamond DA62",
    "SR20": "Cirrus SR20",
    "SR22": "Cirrus SR22"
}

# Canadian private jet manufacturers
CANADIAN_PRIVATE_JET_MANUFACTURERS = ["Bombardier"]

def get_aircraft_type_name(aircraft_code: str) -> str:
    """Get aircraft type name from code, or return original if not found."""
    if aircraft_code in AIRCRAFT_TYPES:
        return AIRCRAFT_TYPES[aircraft_code]
    elif aircraft_code in PRIVATE_JET_CODES:
        return PRIVATE_JET_CODES[aircraft_code]
    return aircraft_code

def is_private_jet(aircraft_code: str) -> bool:
    """Check if aircraft code represents a private jet."""
    return aircraft_code in PRIVATE_JET_CODES

def is_canadian_private_jet(aircraft_type: str) -> bool:
    """Check if aircraft type is a Canadian private jet (Bombardier)."""
    return any(manufacturer in aircraft_type for manufacturer in CANADIAN_PRIVATE_JET_MANUFACTURERS)

class FlightLogic:
    """Handles flight data and runway logic with simplified timing."""
    
    def __init__(self):
        # FlightRadar24 API endpoints
        self.flight_search_url = f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds={config.BOUNDS_BOX}{config.FLIGHT_SEARCH_TAIL}"
    
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
        Get flight data for approach corridor using FlightRadar24 API.
        
        Returns:
            dict: Flight data or None if no flights found
        """
        try:
            response = requests.get(
                url=self.flight_search_url, 
                headers=config.REQUEST_HEADERS, 
                timeout=config.CONNECTION_TIMEOUT
            )
            
            if response.status_code != 200:
                print(f"FlightRadar24 API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            # Look for flight data (skip version and full_count keys)
            for flight_id, flight_info in data.items():
                if flight_id not in ['version', 'full_count'] and isinstance(flight_info, list):
                    if len(flight_info) >= 13:  # Valid flight data
                        # Check altitude filter
                        altitude = flight_info[4] if len(flight_info) > 4 else 0
                        if altitude < config.MAX_APPROACH_ALTITUDE:
                            # Parse flight information
                            flight_data = self._parse_flight_data(flight_id, flight_info)
                            if flight_data:
                                return flight_data
            
            # No valid flights found
            return None
            
        except Exception as e:
            print(f"Error fetching flights from FlightRadar24: {e}")
            return None
    
    def _parse_flight_data(self, flight_id: str, flight_info: List) -> Optional[Dict[str, Any]]:
        """Parse FlightRadar24 API response into structured format."""
        try:
            if len(flight_info) < 13:
                return None
            
            # Extract flight details from FlightRadar24 format
            # Format: [lat, lon, heading, altitude, speed, squawk, radar, aircraft_type, registration, timestamp, origin, destination, flight_number, on_ground, vertical_speed, callsign, is_glider]
            callsign = flight_info[16] if len(flight_info) > 16 else flight_info[13]
            aircraft_type = flight_info[8] if len(flight_info) > 8 else "Unknown"
            altitude = flight_info[4]
            speed = flight_info[5]
            origin = flight_info[11] if len(flight_info) > 11 else "???"
            destination = flight_info[12] if len(flight_info) > 12 else "LGA"
            
            # Get friendly names for display
            friendly_callsign = get_airline_name(callsign or "Unknown")
            friendly_origin = get_airport_name(origin)
            friendly_destination = get_airport_name(destination)
            friendly_aircraft_type = get_aircraft_type_name(aircraft_type)
            
            # Check if this is a private jet
            is_private = is_private_jet(aircraft_type)
            
            return {
                "flight_id": flight_id,
                "callsign": friendly_callsign,
                "aircraft_type": friendly_aircraft_type,
                "altitude": altitude,
                "speed": speed,
                "origin": origin,
                "destination": destination,
                "route": f"{friendly_origin} → {friendly_destination}",
                "is_private_jet": is_private
            }
            
        except Exception as e:
            print(f"Error parsing FlightRadar24 data: {e}")
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