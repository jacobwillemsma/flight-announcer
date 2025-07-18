#!/usr/bin/env python3
"""
Test script to verify double buffering and selective updating performance.
"""

import time
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from display_controller import DisplayController
import config

def test_double_buffering():
    """Test double buffering functionality."""
    print("Testing double buffering...")
    
    # Create a new display controller instance for testing
    display = DisplayController()
    
    # Test 1: Basic text rendering with buffering
    print("\n1. Testing text rendering with double buffering:")
    start_time = time.time()
    
    flight_data = {
        "callsign": "UAL123",
        "aircraft_type": "B738",
        "altitude": 3500,
        "route": "ORD-LGA"
    }
    
    display.show_flight_info(flight_data)
    end_time = time.time()
    
    print(f"   Time taken: {(end_time - start_time)*1000:.2f}ms")
    print(f"   Dirty pixels: {display.get_dirty_pixel_count()}")
    
    # Test 2: Selective updating
    print("\n2. Testing selective pixel updating:")
    start_time = time.time()
    
    # Make a small change - update just the altitude
    flight_data["altitude"] = 3600
    display.show_flight_info(flight_data)
    
    end_time = time.time()
    print(f"   Time taken: {(end_time - start_time)*1000:.2f}ms")
    print(f"   Dirty pixels: {display.get_dirty_pixel_count()}")
    
    # Test 3: Full screen update vs selective update
    print("\n3. Comparing full update vs selective update:")
    
    # Force a full update
    start_time = time.time()
    display._force_full_update()
    end_time = time.time()
    full_update_time = end_time - start_time
    
    print(f"   Full update time: {full_update_time*1000:.2f}ms")
    
    # Now test selective update
    display.set_pixel(10, 10, (255, 0, 0))
    display.set_pixel(11, 10, (0, 255, 0))
    display.set_pixel(12, 10, (0, 0, 255))
    
    start_time = time.time()
    display._swap_buffers()
    end_time = time.time()
    selective_update_time = end_time - start_time
    
    print(f"   Selective update time: {selective_update_time*1000:.2f}ms")
    print(f"   Performance improvement: {(full_update_time - selective_update_time)*1000:.2f}ms")
    
    return display

def test_performance_scenarios():
    """Test various performance scenarios."""
    print("\n" + "="*50)
    print("PERFORMANCE TESTING")
    print("="*50)
    
    display = DisplayController()
    
    # Scenario 1: Text-only updates
    print("\n1. Text-only updates:")
    scenarios = [
        {"callsign": "DAL456", "aircraft_type": "A320", "altitude": 2500, "route": "ATL-LGA"},
        {"callsign": "AAL789", "aircraft_type": "B773", "altitude": 4000, "route": "DFW-LGA"},
        {"callsign": "UAL321", "aircraft_type": "B738", "altitude": 3200, "route": "ORD-LGA"}
    ]
    
    total_time = 0
    for i, scenario in enumerate(scenarios):
        start_time = time.time()
        display.show_flight_info(scenario)
        end_time = time.time()
        update_time = end_time - start_time
        total_time += update_time
        
        print(f"   Update {i+1}: {update_time*1000:.2f}ms, {display.get_dirty_pixel_count()} pixels")
    
    print(f"   Average update time: {(total_time/len(scenarios))*1000:.2f}ms")
    
    # Scenario 2: Weather updates
    print("\n2. Weather display updates:")
    weather_scenarios = [
        {"metar": "KLGA 181851Z 18006KT 10SM CLR 29/22 A2995", "arrivals_runway": "04", "departures_runway": "04"},
        {"metar": "KLGA 181851Z 25009G19KT 10SM RA BKN020 OVC035 22/18 A2987", "arrivals_runway": "04", "departures_runway": "04"},
        {"metar": "KLGA 181851Z 32012KT 10SM TSRA SCT025 BKN040 CB060 25/20 A2980", "arrivals_runway": "04", "departures_runway": "04"}
    ]
    
    total_time = 0
    for i, scenario in enumerate(weather_scenarios):
        start_time = time.time()
        display.show_weather_info(scenario)
        end_time = time.time()
        update_time = end_time - start_time
        total_time += update_time
        
        print(f"   Update {i+1}: {update_time*1000:.2f}ms, {display.get_dirty_pixel_count()} pixels")
    
    print(f"   Average update time: {(total_time/len(weather_scenarios))*1000:.2f}ms")
    
    # Scenario 3: Drawing primitives
    print("\n3. Drawing primitives performance:")
    
    # Test line drawing
    start_time = time.time()
    display.draw_line(0, 0, 127, 31, (255, 255, 255))
    end_time = time.time()
    print(f"   Line drawing: {(end_time - start_time)*1000:.2f}ms")
    
    # Test rectangle drawing
    start_time = time.time()
    display.draw_rectangle(10, 10, 20, 10, (255, 0, 0), filled=True)
    end_time = time.time()
    print(f"   Filled rectangle: {(end_time - start_time)*1000:.2f}ms")
    
    # Test buffer swap
    start_time = time.time()
    display._swap_buffers()
    end_time = time.time()
    print(f"   Buffer swap: {(end_time - start_time)*1000:.2f}ms")

def print_summary():
    """Print implementation summary."""
    print("\n" + "="*50)
    print("IMPLEMENTATION SUMMARY")
    print("="*50)
    
    print("\n✓ Double Buffering System:")
    print("  - Front buffer: Currently displayed content")
    print("  - Back buffer: Content being prepared")
    print("  - Atomic swaps prevent flickering")
    
    print("\n✓ Selective Pixel Updating:")
    print("  - Dirty pixel tracking with set() for O(1) operations")
    print("  - Dirty region tracking for bulk updates")
    print("  - Only changed pixels are updated on hardware")
    
    print("\n✓ Performance Optimizations:")
    print("  - Reduced hardware write operations")
    print("  - Minimal memory allocations")
    print("  - Efficient pixel coordinate tracking")
    
    print("\n✓ Additional Features:")
    print("  - Drawing primitives (lines, rectangles)")
    print("  - Buffer size and dirty pixel queries")
    print("  - Hardware readiness checking")
    
    print(f"\nDisplay Configuration:")
    print(f"  - Resolution: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
    print(f"  - Total pixels: {config.DISPLAY_WIDTH * config.DISPLAY_HEIGHT}")
    print(f"  - Hardware mapping: {config.MATRIX_HARDWARE_MAPPING}")

if __name__ == "__main__":
    try:
        print("LED Matrix Display Performance Test")
        print("=" * 50)
        
        # Test double buffering
        test_double_buffering()
        
        # Test performance scenarios
        test_performance_scenarios()
        
        # Print summary
        print_summary()
        
        print("\n" + "="*50)
        print("PERFORMANCE TEST COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()