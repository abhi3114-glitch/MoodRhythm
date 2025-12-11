"""
Data Store Module
SQLite-based storage for typing timing logs.
Privacy-focused: stores only timing metadata, never actual keystrokes.
"""

import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class DataStore:
    """
    SQLite database for storing typing timing logs.
    Only stores timing metadata - no keystroke text is ever saved.
    """
    
    def __init__(self, db_path: str = "mood_rhythm.db"):
        """
        Initialize the data store.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create typing_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS typing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                interval REAL,
                is_pause BOOLEAN,
                is_burst BOOLEAN,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table for session metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time REAL NOT NULL,
                end_time REAL,
                total_keypresses INTEGER DEFAULT 0,
                avg_wpm REAL,
                mood_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON typing_logs(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session ON typing_logs(session_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_events(self, events: List[Dict]):
        """
        Save a batch of typing events to the database.
        
        Args:
            events: List of event dictionaries with timing data.
        """
        if not events:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            cursor.execute('''
                INSERT INTO typing_logs (timestamp, interval, is_pause, is_burst, session_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                event['timestamp'],
                event.get('interval'),
                event.get('is_pause', False),
                event.get('is_burst', False),
                event.get('session_id')
            ))
        
        conn.commit()
        conn.close()
    
    def save_session(self, session_data: Dict):
        """
        Save session metadata.
        
        Args:
            session_data: Dictionary with session information.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, start_time, end_time, total_keypresses, avg_wpm, mood_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_data['session_id'],
            session_data.get('start_time'),
            session_data.get('end_time'),
            session_data.get('total_keypresses', 0),
            session_data.get('avg_wpm'),
            session_data.get('mood_score')
        ))
        
        conn.commit()
        conn.close()
    
    def get_events(self, 
                   session_id: Optional[str] = None,
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None,
                   limit: int = 10000) -> List[Dict]:
        """
        Retrieve typing events from the database.
        
        Args:
            session_id: Filter by session ID.
            start_time: Filter events after this timestamp.
            end_time: Filter events before this timestamp.
            limit: Maximum number of events to return.
        
        Returns:
            List of event dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM typing_logs WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_events_last_n_days(self, days: int = 7) -> List[Dict]:
        """
        Get events from the last N days.
        
        Args:
            days: Number of days to look back.
        
        Returns:
            List of event dictionaries.
        """
        cutoff = (datetime.now() - timedelta(days=days)).timestamp() * 1000
        return self.get_events(start_time=cutoff)
    
    def get_sessions(self, limit: int = 50) -> List[Dict]:
        """
        Get recent sessions.
        
        Args:
            limit: Maximum number of sessions to return.
        
        Returns:
            List of session dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sessions 
            ORDER BY start_time DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """
        Get aggregated daily statistics.
        
        Args:
            days: Number of days to aggregate.
        
        Returns:
            List of daily stat dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).timestamp() * 1000
        
        cursor.execute('''
            SELECT 
                date(timestamp/1000, 'unixepoch', 'localtime') as day,
                COUNT(*) as keypress_count,
                AVG(interval) as avg_interval,
                SUM(CASE WHEN is_pause THEN 1 ELSE 0 END) as pause_count,
                SUM(CASE WHEN is_burst THEN 1 ELSE 0 END) as burst_count
            FROM typing_logs
            WHERE timestamp >= ?
            GROUP BY day
            ORDER BY day
        ''', (cutoff,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'day': row[0],
                'keypress_count': row[1],
                'avg_interval': row[2],
                'pause_count': row[3],
                'burst_count': row[4]
            }
            for row in rows
        ]
    
    def get_hourly_stats(self, days: int = 7) -> List[Dict]:
        """
        Get aggregated hourly statistics for heatmap.
        
        Args:
            days: Number of days to aggregate.
        
        Returns:
            List of hourly stat dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).timestamp() * 1000
        
        cursor.execute('''
            SELECT 
                strftime('%w', timestamp/1000, 'unixepoch', 'localtime') as day_of_week,
                strftime('%H', timestamp/1000, 'unixepoch', 'localtime') as hour,
                COUNT(*) as keypress_count,
                AVG(interval) as avg_interval
            FROM typing_logs
            WHERE timestamp >= ?
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        ''', (cutoff,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'day_of_week': int(row[0]),
                'hour': int(row[1]),
                'keypress_count': row[2],
                'avg_interval': row[3]
            }
            for row in rows
        ]
    
    def clear_all_data(self):
        """Clear all data from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM typing_logs")
        cursor.execute("DELETE FROM sessions")
        
        conn.commit()
        conn.close()
    
    def get_total_stats(self) -> Dict:
        """Get overall statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_keypresses,
                AVG(interval) as avg_interval,
                SUM(CASE WHEN is_pause THEN 1 ELSE 0 END) as total_pauses,
                SUM(CASE WHEN is_burst THEN 1 ELSE 0 END) as total_bursts,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM typing_logs
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_keypresses': row[0] or 0,
            'avg_interval': row[1] or 0,
            'total_pauses': row[2] or 0,
            'total_bursts': row[3] or 0,
            'first_event': row[4],
            'last_event': row[5]
        }


if __name__ == '__main__':
    # Test the data store
    store = DataStore("test_mood_rhythm.db")
    
    # Test saving events
    test_events = [
        {'timestamp': 1000, 'interval': None, 'is_pause': False, 'is_burst': False, 'session_id': 'test-1'},
        {'timestamp': 1100, 'interval': 100, 'is_pause': False, 'is_burst': False, 'session_id': 'test-1'},
        {'timestamp': 1150, 'interval': 50, 'is_pause': False, 'is_burst': False, 'session_id': 'test-1'},
        {'timestamp': 1180, 'interval': 30, 'is_pause': False, 'is_burst': True, 'session_id': 'test-1'},
    ]
    
    store.save_events(test_events)
    print("Saved test events")
    
    # Retrieve events
    events = store.get_events()
    print(f"Retrieved {len(events)} events")
    
    # Cleanup test db
    os.remove("test_mood_rhythm.db")
    print("Test completed successfully")
