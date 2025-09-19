"""
Database operations for the Smart Temple People Counter.
Handles SQLite database setup, table creation, and CRUD operations for logging entry/exit events.
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import pandas as pd

from utils.config import get_config
from utils.logger import log_database_operation, default_logger


class DatabaseManager:
    """
    Manages all database operations for the people counter system.
    """
    
    def __init__(self, db_path: str = None, logger: logging.Logger = None):
        """
        Initialize database manager.
        
        Args:
            db_path (str): Path to SQLite database file
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.db_path = db_path or self.config.DATABASE_PATH
        self.logger = logger or default_logger
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        event_type TEXT NOT NULL,
                        person_id INTEGER,
                        count_inside INTEGER NOT NULL,
                        total_entered INTEGER NOT NULL,
                        total_exited INTEGER NOT NULL,
                        confidence REAL,
                        notes TEXT
                    )
                """)
                
                # Create daily_summary table for faster reporting
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_summary (
                        date DATE PRIMARY KEY,
                        total_entries INTEGER NOT NULL DEFAULT 0,
                        total_exits INTEGER NOT NULL DEFAULT 0,
                        peak_count INTEGER NOT NULL DEFAULT 0,
                        peak_time DATETIME,
                        avg_count REAL DEFAULT 0,
                        first_entry DATETIME,
                        last_exit DATETIME,
                        total_visit_duration INTEGER DEFAULT 0
                    )
                """)
                
                # Create hourly_stats table for detailed analytics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hourly_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        hour INTEGER NOT NULL,
                        entries INTEGER NOT NULL DEFAULT 0,
                        exits INTEGER NOT NULL DEFAULT 0,
                        peak_count INTEGER NOT NULL DEFAULT 0,
                        avg_count REAL DEFAULT 0,
                        UNIQUE(date, hour)
                    )
                """)
                
                # Create alerts table for tracking alert history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        alert_type TEXT NOT NULL,
                        current_count INTEGER NOT NULL,
                        threshold INTEGER NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_timestamp DATETIME,
                        notes TEXT
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_summary(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hourly_stats_date_hour ON hourly_stats(date, hour)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
                
                conn.commit()
                log_database_operation(self.logger, "Database initialization", True)
                
        except Exception as e:
            log_database_operation(self.logger, "Database initialization", False, str(e))
            raise
    
    def log_event(self, event_type: str, person_id: int, count_inside: int, 
                  total_entered: int, total_exited: int, confidence: float = None, 
                  notes: str = None) -> int:
        """
        Log a people counting event to the database.
        
        Args:
            event_type (str): 'entry', 'exit', or 'reset'
            person_id (int): Unique identifier for the person
            count_inside (int): Current count of people inside
            total_entered (int): Total number of people who have entered
            total_exited (int): Total number of people who have exited
            confidence (float): Detection confidence score
            notes (str): Additional notes
        
        Returns:
            int: ID of the inserted event record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO events (timestamp, event_type, person_id, count_inside, 
                                      total_entered, total_exited, confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    event_type,
                    person_id,
                    count_inside,
                    total_entered,
                    total_exited,
                    confidence,
                    notes
                ))
                
                event_id = cursor.lastrowid
                conn.commit()
                
                # Update daily and hourly statistics
                self._update_statistics(event_type, count_inside)
                
                log_database_operation(self.logger, f"Event logged: {event_type}", True)
                return event_id
                
        except Exception as e:
            log_database_operation(self.logger, f"Log event: {event_type}", False, str(e))
            raise
    
    def log_alert(self, alert_type: str, current_count: int, threshold: int, 
                  notes: str = None) -> int:
        """
        Log an alert to the database.
        
        Args:
            alert_type (str): Type of alert ('warning', 'limit_exceeded', etc.)
            current_count (int): Current people count
            threshold (int): Threshold that triggered the alert
            notes (str): Additional notes
        
        Returns:
            int: ID of the inserted alert record
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (timestamp, alert_type, current_count, threshold, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (datetime.now(), alert_type, current_count, threshold, notes))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                log_database_operation(self.logger, f"Alert logged: {alert_type}", True)
                return alert_id
                
        except Exception as e:
            log_database_operation(self.logger, f"Log alert: {alert_type}", False, str(e))
            raise
    
    def get_current_count(self) -> Dict[str, int]:
        """
        Get the current people count from the last recorded event.
        
        Returns:
            Dict with current statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT count_inside, total_entered, total_exited
                    FROM events
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "count_inside": result[0],
                        "total_entered": result[1],
                        "total_exited": result[2]
                    }
                else:
                    return {"count_inside": 0, "total_entered": 0, "total_exited": 0}
                    
        except Exception as e:
            log_database_operation(self.logger, "Get current count", False, str(e))
            return {"count_inside": 0, "total_entered": 0, "total_exited": 0}
    
    def get_daily_stats(self, target_date: date = None) -> Dict[str, Any]:
        """
        Get statistics for a specific date.
        
        Args:
            target_date (date): Date to get stats for (default: today)
        
        Returns:
            Dict with daily statistics
        """
        if not target_date:
            target_date = date.today()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get from daily_summary table first
                cursor.execute("""
                    SELECT total_entries, total_exits, peak_count, peak_time,
                           avg_count, first_entry, last_exit
                    FROM daily_summary
                    WHERE date = ?
                """, (target_date,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "date": target_date,
                        "total_entries": result[0],
                        "total_exits": result[1],
                        "peak_count": result[2],
                        "peak_time": result[3],
                        "avg_count": result[4],
                        "first_entry": result[5],
                        "last_exit": result[6]
                    }
                else:
                    # Calculate from events table if summary doesn't exist
                    return self._calculate_daily_stats(target_date)
                    
        except Exception as e:
            log_database_operation(self.logger, f"Get daily stats for {target_date}", False, str(e))
            return {}
    
    def get_events_by_date_range(self, start_date: date, end_date: date = None) -> List[Dict]:
        """
        Get events within a date range.
        
        Args:
            start_date (date): Start date
            end_date (date): End date (default: same as start_date)
        
        Returns:
            List of event dictionaries
        """
        if not end_date:
            end_date = start_date
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, timestamp, event_type, person_id, count_inside,
                           total_entered, total_exited, confidence, notes
                    FROM events
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start_date, end_date))
                
                events = []
                for row in cursor.fetchall():
                    events.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "event_type": row[2],
                        "person_id": row[3],
                        "count_inside": row[4],
                        "total_entered": row[5],
                        "total_exited": row[6],
                        "confidence": row[7],
                        "notes": row[8]
                    })
                
                return events
                
        except Exception as e:
            log_database_operation(self.logger, f"Get events {start_date} to {end_date}", False, str(e))
            return []
    
    def reset_counts(self, notes: str = "Manual reset") -> bool:
        """
        Reset all counts to zero and log the reset event.
        
        Args:
            notes (str): Reason for reset
        
        Returns:
            bool: Success status
        """
        try:
            current_stats = self.get_current_count()
            
            # Log the reset event
            self.log_event(
                event_type="reset",
                person_id=-1,
                count_inside=0,
                total_entered=current_stats["total_entered"],
                total_exited=current_stats["total_exited"],
                notes=notes
            )
            
            log_database_operation(self.logger, "Reset counts", True)
            return True
            
        except Exception as e:
            log_database_operation(self.logger, "Reset counts", False, str(e))
            return False
    
    def get_hourly_distribution(self, target_date: date = None) -> List[Dict]:
        """
        Get hourly distribution of visitors for a specific date.
        
        Args:
            target_date (date): Date to analyze (default: today)
        
        Returns:
            List of hourly statistics
        """
        if not target_date:
            target_date = date.today()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT hour, entries, exits, peak_count, avg_count
                    FROM hourly_stats
                    WHERE date = ?
                    ORDER BY hour
                """, (target_date,))
                
                hourly_data = []
                for row in cursor.fetchall():
                    hourly_data.append({
                        "hour": row[0],
                        "entries": row[1],
                        "exits": row[2],
                        "peak_count": row[3],
                        "avg_count": row[4]
                    })
                
                return hourly_data
                
        except Exception as e:
            log_database_operation(self.logger, f"Get hourly distribution for {target_date}", False, str(e))
            return []
    
    def export_to_dataframe(self, start_date: date, end_date: date = None) -> pd.DataFrame:
        """
        Export events data to pandas DataFrame for analysis.
        
        Args:
            start_date (date): Start date
            end_date (date): End date (default: same as start_date)
        
        Returns:
            pandas.DataFrame: Events data
        """
        if not end_date:
            end_date = start_date
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT timestamp, event_type, person_id, count_inside,
                           total_entered, total_exited, confidence
                    FROM events
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
                
        except Exception as e:
            log_database_operation(self.logger, f"Export to DataFrame {start_date} to {end_date}", False, str(e))
            return pd.DataFrame()
    
    def _update_statistics(self, event_type: str, count_inside: int):
        """Update daily and hourly statistics tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                current_time = datetime.now()
                current_date = current_time.date()
                current_hour = current_time.hour
                
                # Update daily summary
                if event_type in ['entry', 'exit']:
                    cursor.execute("""
                        INSERT OR IGNORE INTO daily_summary (date) VALUES (?)
                    """, (current_date,))
                    
                    if event_type == 'entry':
                        cursor.execute("""
                            UPDATE daily_summary 
                            SET total_entries = total_entries + 1,
                                peak_count = MAX(peak_count, ?),
                                first_entry = COALESCE(first_entry, ?)
                            WHERE date = ?
                        """, (count_inside, current_time, current_date))
                    
                    elif event_type == 'exit':
                        cursor.execute("""
                            UPDATE daily_summary 
                            SET total_exits = total_exits + 1,
                                last_exit = ?
                            WHERE date = ?
                        """, (current_time, current_date))
                
                # Update hourly stats
                cursor.execute("""
                    INSERT OR REPLACE INTO hourly_stats 
                    (date, hour, entries, exits, peak_count)
                    VALUES (?, ?, 
                            COALESCE((SELECT entries FROM hourly_stats WHERE date=? AND hour=?), 0) + ?,
                            COALESCE((SELECT exits FROM hourly_stats WHERE date=? AND hour=?), 0) + ?,
                            MAX(COALESCE((SELECT peak_count FROM hourly_stats WHERE date=? AND hour=?), 0), ?))
                """, (
                    current_date, current_hour,
                    current_date, current_hour, 1 if event_type == 'entry' else 0,
                    current_date, current_hour, 1 if event_type == 'exit' else 0,
                    current_date, current_hour, count_inside
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _calculate_daily_stats(self, target_date: date) -> Dict[str, Any]:
        """Calculate daily statistics from events table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count entries and exits
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN event_type = 'entry' THEN 1 ELSE 0 END) as entries,
                        SUM(CASE WHEN event_type = 'exit' THEN 1 ELSE 0 END) as exits,
                        MAX(count_inside) as peak_count
                    FROM events
                    WHERE DATE(timestamp) = ?
                """, (target_date,))
                
                result = cursor.fetchone()
                
                return {
                    "date": target_date,
                    "total_entries": result[0] or 0,
                    "total_exits": result[1] or 0,
                    "peak_count": result[2] or 0,
                    "peak_time": None,
                    "avg_count": 0,
                    "first_entry": None,
                    "last_exit": None
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating daily stats: {e}")
            return {}


# Global database manager instance
db_manager = DatabaseManager()

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager