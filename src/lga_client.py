#!/usr/bin/env python3
"""
LGA Airport Information Client
Clean client for fetching LGA runway and weather information.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

ATIS_URL = "https://datis.clowd.io/api/KLGA"
METAR_URL = "https://aviationweather.gov/api/data/metar?ids=KLGA&format=json"

def get_current_metar() -> Optional[str]:
    """
    Get current METAR rawOb from Aviation Weather API.
    
    Returns:
        str: METAR rawOb string (e.g., "KLGA 160151Z 18006KT 10SM FEW050 SCT250 27/22 A3004 RMK AO2 SLP173 T02670217")
        None: If unable to fetch or parse data
    """
    try:
        with urllib.request.urlopen(METAR_URL, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    return data[0].get("rawOb", "")
        return None
    except Exception as e:
        print(f"Error fetching METAR data: {e}")
        return None

def get_atis_text() -> Optional[str]:
    """
    Get current ATIS text from LGA ATIS feed.
    
    Returns:
        str: Full ATIS text
        None: If unable to fetch data
    """
    try:
        with urllib.request.urlopen(ATIS_URL, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    return data[0].get("datis", "")
        return None
    except Exception as e:
        print(f"Error fetching ATIS data: {e}")
        return None

def get_active_runways() -> Dict[str, Optional[str]]:
    """
    Get current active runways from LGA ATIS.
    
    Returns:
        dict: {"arrivals": "22", "departures": "13"} or None values if unavailable
    """
    try:
        # Fetch ATIS data
        with urllib.request.urlopen(ATIS_URL, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    atis_text = data[0].get("datis", "").upper()
                
                # Parse landing (arrivals) runway
                arrivals = _parse_landing_runway(atis_text)
                
                # Parse departure runway
                departures = _parse_departure_runway(atis_text)
                
                return {
                    "arrivals": arrivals,
                    "departures": departures
                }
        
        return {"arrivals": None, "departures": None}
        
    except Exception as e:
        print(f"Error fetching ATIS data: {e}")
        return {"arrivals": None, "departures": None}

def _parse_landing_runway(atis_text: str) -> Optional[str]:
    """
    Parse ATIS text to extract the landing runway.
    
    Common patterns:
    - "LND RY 22"
    - "ILS RY 22 APCH IN USE LND RY 22"
    - "LANDING RUNWAY 04"
    - "LND RWY 13"
    """
    if not atis_text:
        return None
    
    text = atis_text.upper()
    
    # Pattern 1: "LND RY XX" or "LND RWY XX"
    pattern1 = r'LND\s+RW?Y\s+(\d+[LCR]?)'
    match = re.search(pattern1, text)
    if match:
        return match.group(1)
    
    # Pattern 2: "LANDING RUNWAY XX" or "LANDING RY XX"
    pattern2 = r'LANDING\s+RW?Y\s+(\d+[LCR]?)'
    match = re.search(pattern2, text)
    if match:
        return match.group(1)
    
    # Pattern 3: "ILS RY XX APCH IN USE" (implies landing on that runway)
    pattern3 = r'ILS\s+RW?Y\s+(\d+[LCR]?)\s+APCH\s+IN\s+USE'
    match = re.search(pattern3, text)
    if match:
        return match.group(1)
    
    # Pattern 4: Look for "APCH IN USE" after runway mention
    pattern4 = r'RW?Y\s+(\d+[LCR]?)\s+APCH\s+IN\s+USE'
    match = re.search(pattern4, text)
    if match:
        return match.group(1)
    
    return None

def _parse_departure_runway(atis_text: str) -> Optional[str]:
    """Parse ATIS text to extract the departure runway."""
    if not atis_text:
        return None
    
    text = atis_text.upper()
    
    # Pattern: "DEPART RY XX" or "DEP RWY XX"
    pattern = r'(?:DEPART|DEP)\s+RW?Y\s+(\d+[LCR]?)'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    
    return None


if __name__ == "__main__":
    print("LGA Airport Information Client")
    print("=" * 40)
    
    # Test METAR
    print("Current Weather:")
    print("-" * 20)
    metar = get_current_metar()
    if metar:
        print(f"✅ METAR: {metar}")
    else:
        print("❌ Could not fetch METAR")
    print()
    
    # Test runway information
    print("Active Runways:")
    print("-" * 20)
    runways = get_active_runways()
    print(f"Arrivals:   {runways['arrivals'] or 'Unknown'}")
    print(f"Departures: {runways['departures'] or 'Unknown'}")
    print()
    
    # Show example usage
    print("Example Usage:")
    print("-" * 20)
    print("from lga_client import get_current_metar, get_active_runways")
    print()
    print("# Get weather")
    print("metar = get_current_metar()")
    print(f"# Returns: '{metar}'")
    print()
    print("# Get runways")
    print("runways = get_active_runways()")
    print(f"# Returns: {runways}")