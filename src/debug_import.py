#!/usr/bin/env python3

import sys
import os
print("Python executable:", sys.executable)
print("Working directory:", os.getcwd())
print("Python path:")
for p in sys.path:
    print(f"  {p}")
print()

try:
    from flight_logic import flight_logic
    print("✅ flight_logic imported")
except Exception as e:
    print(f"❌ flight_logic failed: {e}")

try:
    from display_controller import display_controller
    print("✅ display_controller imported")
except Exception as e:
    print(f"❌ display_controller failed: {e}")

try:
    from stats_tracker import FlightStatsTracker
    print("✅ FlightStatsTracker imported")
except Exception as e:
    print(f"❌ FlightStatsTracker failed: {e}")
    import traceback
    traceback.print_exc()

try:
    import config
    print("✅ config imported")
except Exception as e:
    print(f"❌ config failed: {e}")