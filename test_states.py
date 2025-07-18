#!/usr/bin/env python3
"""
Test States for Flight Announcer Display
Easy testing of all possible display states without needing live data.
"""

import sys
import os
sys.path.append('src')

from display_controller import display_controller

def test_sunny_weather():
    """Test sunny weather display."""
    print("Testing Sunny Weather Display...")
    
    weather_data = {
        "type": "weather",
        "arrivals_runway": "04L",
        "departures_runway": "04R", 
        "metar": "KLGA 181851Z 25012KT 10SM CLR 29/22 A2995 RMK AO2"
    }
    
    display_controller.show_weather_info(weather_data)
    print("✅ Sunny weather test complete\n")

def test_windy_weather():
    """Test windy/cloudy weather display."""
    print("Testing Windy Weather Display...")
    
    weather_data = {
        "type": "weather",
        "arrivals_runway": "13",
        "departures_runway": "31",
        "metar": "KLGA 180251Z 30013KT 10SM BKN250 29/18 A2984 RMK AO2"
    }
    
    display_controller.show_weather_info(weather_data)
    print("✅ Windy weather test complete\n")

def test_rainy_weather():
    """Test rainy weather display."""
    print("Testing Rainy Weather Display...")
    
    weather_data = {
        "type": "weather", 
        "arrivals_runway": "22",
        "departures_runway": "04",
        "metar": "KLGA 181851Z 18006KT 5SM RA BKN015 OVC025 18/16 A2995 RMK AO2"
    }
    
    display_controller.show_weather_info(weather_data)
    print("✅ Rainy weather test complete\n")

def test_approaching_plane():
    """Test approaching plane display."""
    print("Testing Approaching Plane Display...")
    
    flight_data = {
        "type": "flight",
        "flight_id": "test123",
        "callsign": "JBU1234",
        "aircraft_type": "A320",
        "altitude": 2500,
        "speed": 180,
        "origin": "BOS",
        "destination": "LGA",
        "route": "BOS → LGA"
    }
    
    display_controller.show_flight_info(flight_data)
    print("✅ Approaching plane test complete\n")

def test_plane_celebration():
    """Test plane detection celebration sequence."""
    print("Testing Plane Detection Celebration...")
    
    flight_data = {
        "type": "flight",
        "flight_id": "celebrate123",
        "callsign": "UAL456",
        "aircraft_type": "B737",
        "altitude": 1800,
        "speed": 160,
        "origin": "ORD",
        "destination": "LGA",
        "route": "ORD → LGA"
    }
    
    display_controller.show_plane_celebration(flight_data)
    input("Press Enter to finish...")
    print("✅ Plane celebration test complete\n")

def test_no_flights():
    """Test no flights detected message."""
    print("Testing No Flights Display...")
    
    message_data = {
        "type": "no_flights",
        "message": "No Approach Traffic Detected",
        "runway_status": {
            "arrivals": "04L",
            "departures": "04R"
        }
    }
    
    display_controller.show_no_flights_message(message_data)
    print("✅ No flights test complete\n")

def test_all_states():
    """Test all display states in sequence."""
    print("="*60)
    print("TESTING ALL DISPLAY STATES")
    print("="*60)
    
    test_sunny_weather()
    input("Press Enter to continue to windy weather...")
    
    test_windy_weather()
    input("Press Enter to continue to rainy weather...")
    
    test_rainy_weather()
    input("Press Enter to continue to approaching plane...")
    
    test_approaching_plane()
    input("Press Enter to continue to plane celebration...")
    
    test_plane_celebration()
    input("Press Enter to continue to no flights...")
    
    test_no_flights()
    input("Press Enter to finish...")
    
    print("="*60)
    print("ALL TESTS COMPLETE!")
    print("="*60)

def interactive_menu():
    """Interactive menu for testing specific states."""
    while True:
        print("\n" + "="*50)
        print("FLIGHT ANNOUNCER DISPLAY TESTER")
        print("="*50)
        print("1. Test Sunny Weather")
        print("2. Test Windy Weather") 
        print("3. Test Rainy Weather")
        print("4. Test Approaching Plane")
        print("5. Test Plane Celebration")
        print("6. Test No Flights")
        print("7. Test All States")
        print("8. Clear Display")
        print("0. Exit")
        print("="*50)
        
        choice = input("Select option (0-8): ").strip()
        
        if choice == "1":
            test_sunny_weather()
        elif choice == "2":
            test_windy_weather()
        elif choice == "3":
            test_rainy_weather()
        elif choice == "4":
            test_approaching_plane()
        elif choice == "5":
            test_plane_celebration()
        elif choice == "6":
            test_no_flights()
        elif choice == "7":
            test_all_states()
        elif choice == "8":
            display_controller.clear_display()
            print("✅ Display cleared\n")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    print("Flight Announcer Display State Tester")
    print("=====================================")
    
    # Check if running with arguments
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        if test_name == "sunny":
            test_sunny_weather()
        elif test_name == "windy":
            test_windy_weather()
        elif test_name == "rainy":
            test_rainy_weather()
        elif test_name == "plane":
            test_approaching_plane()
        elif test_name == "celebration":
            test_plane_celebration()
        elif test_name == "no_flights":
            test_no_flights()
        elif test_name == "all":
            test_all_states()
        else:
            print(f"Unknown test: {test_name}")
            print("Usage: python test_states.py [sunny|windy|rainy|plane|celebration|no_flights|all]")
    else:
        # Run interactive menu
        interactive_menu()