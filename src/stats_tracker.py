import sqlite3
import json
import threading
from datetime import datetime, date
from typing import Dict, Any, Optional
from pathlib import Path

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
    
    def get_daily_stats(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date_str,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    'date': date_str,
                    'numberOfPlanes': 0,
                    'numberOfHelicopters': 0,
                    'numberOfPrivateJets': 0,
                    'byOrigin': {},
                    'byAirline': {},
                    'byAircraftType': {}
                }
            
            return {
                'date': row[0],
                'numberOfPlanes': row[1],
                'numberOfHelicopters': row[2],
                'numberOfPrivateJets': row[3],
                'byOrigin': json.loads(row[4] or '{}'),
                'byAirline': json.loads(row[5] or '{}'),
                'byAircraftType': json.loads(row[6] or '{}')
            }
    
    def get_stats_json_format(self, date_str: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_daily_stats(date_str)
        return {
            date_str: {
                'numberOfPlanes': stats['numberOfPlanes'],
                'numberOfHelicopters': stats['numberOfHelicopters'],
                'numberOfPrivateJets': stats['numberOfPrivateJets'],
                'byOrigin': stats['byOrigin']
            }
        }
    
    def export_to_json_file(self, filename: str = "stats.json", days: int = 30):
        all_stats = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, total_planes, helicopters, private_jets, origins_json 
                FROM daily_stats 
                ORDER BY date DESC 
                LIMIT ?
            """, (days,))
            
            for row in cursor.fetchall():
                date_str = row[0]
                all_stats[date_str] = {
                    'numberOfPlanes': row[1],
                    'numberOfHelicopters': row[2],
                    'numberOfPrivateJets': row[3],
                    'byOrigin': json.loads(row[4] or '{}')
                }
        
        with open(filename, 'w') as f:
            json.dump(all_stats, f, indent=2)
        
        return filename

# Create module-level instance following the same pattern as other modules
try:
    import config
    stats_tracker = FlightStatsTracker(config.STATS_DB_PATH) if config.STATS_ENABLED else None
except:
    stats_tracker = None