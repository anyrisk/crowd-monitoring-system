#!/usr/bin/env python3
"""
SQLite Database Viewer for Crowd Monitoring System
View and analyze the stored data in the SQLite database
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from pathlib import Path

def check_database_exists():
    """Check if database file exists."""
    db_path = "data/database.db"
    if Path(db_path).exists():
        size = Path(db_path).stat().st_size
        print(f"✅ Database found: {db_path}")
        print(f"📁 File size: {size} bytes")
        return db_path
    else:
        print(f"❌ Database not found: {db_path}")
        print("💡 Run the crowd monitoring system first to create the database")
        return None

def show_database_structure(db_path):
    """Show database tables and structure."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n📊 DATABASE STRUCTURE:")
        print("="*50)
        
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("   Columns:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = " (PRIMARY KEY)" if col[5] else ""
                not_null = " NOT NULL" if col[3] else ""
                print(f"     - {col_name}: {col_type}{not_null}{is_pk}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📈 Records: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database structure: {e}")

def show_recent_events(db_path, limit=10):
    """Show recent events from the database."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Get recent events
        query = """
        SELECT timestamp, event_type, person_id, count_inside, 
               total_entered, total_exited, confidence
        FROM events 
        ORDER BY timestamp DESC 
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        
        if not df.empty:
            print(f"\n📋 RECENT EVENTS (Last {limit}):")
            print("="*80)
            print(df.to_string(index=False))
        else:
            print("\n📋 No events found in database")
            print("💡 Start the monitoring system and move in front of the camera to generate events")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading events: {e}")

def show_daily_summary(db_path):
    """Show daily summary statistics."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Get daily summary
        query = """
        SELECT date, total_entries, total_exits, peak_count, 
               peak_time, first_entry, last_exit
        FROM daily_summary 
        ORDER BY date DESC 
        LIMIT 7
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            print(f"\n📊 DAILY SUMMARY (Last 7 days):")
            print("="*80)
            print(df.to_string(index=False))
        else:
            print("\n📊 No daily summary data available")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading daily summary: {e}")

def show_current_counts(db_path):
    """Show current system counts."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get latest counts
        cursor.execute("""
        SELECT count_inside, total_entered, total_exited, timestamp
        FROM events 
        ORDER BY timestamp DESC 
        LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            count_inside, total_entered, total_exited, timestamp = result
            print(f"\n🎯 CURRENT COUNTS:")
            print("="*30)
            print(f"People Inside: {count_inside}")
            print(f"Total Entries: {total_entered}")
            print(f"Total Exits: {total_exited}")
            print(f"Last Update: {timestamp}")
        else:
            print("\n🎯 No count data available")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading current counts: {e}")

def export_data_to_csv(db_path):
    """Export all events to CSV file."""
    try:
        conn = sqlite3.connect(db_path)
        
        # Export events
        df = pd.read_sql_query("SELECT * FROM events ORDER BY timestamp", conn)
        
        if not df.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crowd_data_export_{timestamp}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Data exported to: {filename}")
            print(f"📊 Records exported: {len(df)}")
        else:
            print("\n💾 No data to export")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")

def interactive_database_viewer():
    """Interactive database viewer."""
    print("\n🗄️  CROWD MONITORING SYSTEM - DATABASE VIEWER")
    print("="*60)
    
    # Check if database exists
    db_path = check_database_exists()
    if not db_path:
        return
    
    while True:
        print("\n📋 OPTIONS:")
        print("1. Show database structure")
        print("2. Show recent events")
        print("3. Show daily summary")
        print("4. Show current counts")
        print("5. Export data to CSV")
        print("6. Exit")
        
        choice = input("\n🔍 Enter your choice (1-6): ").strip()
        
        if choice == '1':
            show_database_structure(db_path)
        elif choice == '2':
            limit = input("📊 Number of recent events to show (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            show_recent_events(db_path, limit)
        elif choice == '3':
            show_daily_summary(db_path)
        elif choice == '4':
            show_current_counts(db_path)
        elif choice == '5':
            export_data_to_csv(db_path)
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")

def quick_database_check():
    """Quick database status check."""
    print("\n🗄️  SQLITE DATABASE STATUS")
    print("="*40)
    
    db_path = check_database_exists()
    if db_path:
        show_database_structure(db_path)
        show_current_counts(db_path)
        show_recent_events(db_path, 5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_database_check()
    else:
        interactive_database_viewer()