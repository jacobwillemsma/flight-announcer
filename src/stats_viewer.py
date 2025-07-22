#!/usr/bin/env python3
"""
Flight Stats Viewer
CLI tool for viewing and exporting flight statistics.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

try:
    from stats_tracker import FlightStatsTracker
    import config
except ImportError:
    print("Error: Could not import stats_tracker module")
    print("Make sure you're running this from the src/ directory")
    sys.exit(1)

def format_stats_table(stats_data: dict) -> str:
    """Format stats data into a readable table."""
    output = []
    
    for date_str, data in sorted(stats_data.items()):
        output.append(f"\n📅 {date_str}")
        output.append("=" * 50)
        output.append(f"✈️  Total Planes: {data['numberOfPlanes']}")
        output.append(f"🚁  Helicopters: {data['numberOfHelicopters']}")
        output.append(f"🛩️  Private Jets: {data['numberOfPrivateJets']}")
        
        if data.get('byOrigin'):
            output.append("\n🏢 By Origin:")
            for origin, count in sorted(data['byOrigin'].items(), key=lambda x: x[1], reverse=True):
                output.append(f"   {origin}: {count}")
        
        if data.get('byAirline'):
            output.append("\n✈️  By Airline:")
            for airline, count in sorted(data['byAirline'].items(), key=lambda x: x[1], reverse=True):
                output.append(f"   {airline}: {count}")
        
        if data.get('byAircraftType'):
            output.append("\n🛫 By Aircraft Type:")
            for aircraft_type, count in sorted(data['byAircraftType'].items(), key=lambda x: x[1], reverse=True)[:10]:
                output.append(f"   {aircraft_type}: {count}")
    
    return "\n".join(output)

def show_today_stats(tracker: FlightStatsTracker):
    """Show today's flight statistics."""
    today = datetime.now().strftime("%Y-%m-%d")
    stats = tracker.get_daily_stats(today)
    
    print(f"\n📊 Flight Statistics for {today}")
    print("=" * 60)
    print(f"✈️  Total Planes Detected: {stats['numberOfPlanes']}")
    print(f"🚁  Helicopters: {stats['numberOfHelicopters']}")
    print(f"🛩️  Private Jets: {stats['numberOfPrivateJets']}")
    
    if stats['byOrigin']:
        print(f"\n🏢 Top Origins:")
        for origin, count in sorted(stats['byOrigin'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {origin}: {count}")
    
    if stats.get('byAirline'):
        print(f"\n✈️  Top Airlines:")
        for airline, count in sorted(stats['byAirline'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {airline}: {count}")
    
    if stats.get('byAircraftType'):
        print(f"\n🛫 Top Aircraft Types:")
        for aircraft_type, count in sorted(stats['byAircraftType'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {aircraft_type}: {count}")

def show_weekly_stats(tracker: FlightStatsTracker):
    """Show past week's flight statistics."""
    stats_data = {}
    
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        stats = tracker.get_daily_stats(date)
        if stats['numberOfPlanes'] > 0:
            stats_data[date] = stats
    
    if not stats_data:
        print("No flight data found for the past week.")
        return
    
    print("\n📊 Flight Statistics - Past 7 Days")
    print("=" * 60)
    
    total_planes = sum(data['numberOfPlanes'] for data in stats_data.values())
    total_helicopters = sum(data['numberOfHelicopters'] for data in stats_data.values())
    total_private_jets = sum(data['numberOfPrivateJets'] for data in stats_data.values())
    
    print(f"✈️  Total Planes: {total_planes}")
    print(f"🚁  Total Helicopters: {total_helicopters}")
    print(f"🛩️  Total Private Jets: {total_private_jets}")
    print(f"📅 Days with Activity: {len(stats_data)}")
    
    print(format_stats_table(stats_data))

def export_stats(tracker: FlightStatsTracker, filename: str, days: int):
    """Export statistics to JSON file."""
    try:
        exported_file = tracker.export_to_json_file(filename, days)
        print(f"✅ Statistics exported to: {exported_file}")
        print(f"📊 Data includes last {days} days")
    except Exception as e:
        print(f"❌ Error exporting stats: {e}")

def show_raw_stats(tracker: FlightStatsTracker, date: Optional[str] = None):
    """Show raw statistics data in JSON format."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    stats = tracker.get_stats_json_format(date)
    print(json.dumps(stats, indent=2))

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Flight Statistics Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stats_viewer.py                    # Show today's stats
  python stats_viewer.py --week            # Show past week stats
  python stats_viewer.py --export stats.json  # Export to JSON
  python stats_viewer.py --raw             # Show raw JSON format
  python stats_viewer.py --date 2025-07-21 # Show specific date
        """
    )
    
    parser.add_argument('--week', action='store_true', help='Show past week statistics')
    parser.add_argument('--export', metavar='FILENAME', help='Export stats to JSON file')
    parser.add_argument('--days', type=int, default=30, help='Number of days to export (default: 30)')
    parser.add_argument('--raw', action='store_true', help='Show raw JSON format')
    parser.add_argument('--date', help='Show stats for specific date (YYYY-MM-DD)')
    parser.add_argument('--db-path', default=None, help='Custom database path')
    
    args = parser.parse_args()
    
    # Initialize stats tracker
    db_path = args.db_path or config.STATS_DB_PATH
    try:
        tracker = FlightStatsTracker(db_path)
    except Exception as e:
        print(f"❌ Error initializing stats tracker: {e}")
        print(f"Database path: {db_path}")
        sys.exit(1)
    
    # Handle commands
    if args.export:
        export_stats(tracker, args.export, args.days)
    elif args.week:
        show_weekly_stats(tracker)
    elif args.raw:
        show_raw_stats(tracker, args.date)
    elif args.date:
        stats = tracker.get_daily_stats(args.date)
        stats_data = {args.date: stats}
        print(format_stats_table(stats_data))
    else:
        show_today_stats(tracker)

if __name__ == "__main__":
    main()