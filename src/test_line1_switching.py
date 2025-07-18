#!/usr/bin/env python3

from display_engine import *
import time

# Test if Line 1 is switching between A and B inappropriately
print('Testing Line 1 switching behavior...')
print('=' * 80)

# Mock weather data
weather_data = {
    "arrivals_runway": "31",
    "departures_runway": "04",
    "metar": "METAR KLGA 171651Z 25009G19KT 10SM SCT025 BKN120 BKN250 31/21 A2984",
    "atis_letter": "H"
}

app_data = AppData(
    flight_data=None,
    weather_data=weather_data,
    runway_status=None
)

print('Checking Line 1 content at small intervals around 5-second boundary...')
print('It should stay "NO RWY 04 ARRIVALS" until exactly 5.0s, then switch to "WEATHER AT KLGA:"')
print('-' * 80)

# Test times around the 5-second boundary
test_times = [
    4.8, 4.9, 4.95, 4.99, 5.0, 5.01, 5.05, 5.1, 5.2,
    9.8, 9.9, 9.95, 9.99, 10.0, 10.01, 10.05, 10.1, 10.2
]

for t in test_times:
    # Test Line 1 alone
    line1_alone = alternating_text(["NO RWY 04 ARRIVALS", "WEATHER AT KLGA:"], 5.0, t)
    
    # Test Line 1 with full display
    display_def = compute_display_state(t, app_data)
    line1_with_display = display_def.rows[0].text
    
    # Check if they match
    match = "✅" if line1_alone == line1_with_display else "❌"
    
    print(f't={t:5.2f}s: {match} Alone="{line1_alone}" | WithDisplay="{line1_with_display}"')

print('\n' + '=' * 80)
print('Now testing rapid succession (like scroll ticks)...')
print('Line 1 should stay stable even when called rapidly')
print('-' * 80)

# Test rapid calls between 6.0s and 7.0s (when Line 1 should be stable)
base_time = 6.0
for i in range(20):
    t = base_time + (i * 0.05)  # Every 50ms
    display_def = compute_display_state(t, app_data)
    line1_text = display_def.rows[0].text
    
    if i == 0:
        expected_text = line1_text
    
    stable = "✅" if line1_text == expected_text else "❌"
    print(f't={t:5.2f}s: {stable} "{line1_text}"')

print('\n' + '=' * 80)
print('If Line 1 is switching during rapid calls, we found the bug!')