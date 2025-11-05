#!/usr/bin/env python3
"""
Accuracy Monitoring Tool for Crowd Monitoring System
Tracks system performance and provides accuracy metrics
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

class AccuracyMonitor:
    """Monitor and track system accuracy metrics."""
    
    def __init__(self):
        self.metrics_file = "data/accuracy_metrics.json"
        self.start_time = datetime.now()
        self.metrics = {
            'session_start': self.start_time.isoformat(),
            'total_detections': 0,
            'total_crossings': 0,
            'false_positives': 0,
            'missed_detections': 0,
            'fps_history': [],
            'accuracy_history': [],
            'manual_counts': []
        }
        
    def log_detection(self, detection_count, fps):
        """Log detection metrics."""
        self.metrics['total_detections'] += detection_count
        self.metrics['fps_history'].append({
            'timestamp': datetime.now().isoformat(),
            'fps': fps,
            'detections': detection_count
        })
        
        # Keep only last 100 FPS readings
        if len(self.metrics['fps_history']) > 100:
            self.metrics['fps_history'] = self.metrics['fps_history'][-100:]
    
    def log_crossing(self, crossing_type, object_id):
        """Log crossing event."""
        self.metrics['total_crossings'] += 1
        print(f"📊 Accuracy Monitor: {crossing_type} detected (ID: {object_id})")
        print(f"   Total crossings this session: {self.metrics['total_crossings']}")
    
    def add_manual_count(self, actual_count, notes=""):
        """Add manual verification count."""
        current_system_count = self.get_current_system_count()
        accuracy = (min(actual_count, current_system_count) / max(actual_count, current_system_count)) * 100
        
        manual_entry = {
            'timestamp': datetime.now().isoformat(),
            'actual_count': actual_count,
            'system_count': current_system_count,
            'accuracy': accuracy,
            'notes': notes
        }
        
        self.metrics['manual_counts'].append(manual_entry)
        self.metrics['accuracy_history'].append(accuracy)
        
        print(f"\n📊 ACCURACY CHECK:")
        print(f"   Manual Count: {actual_count}")
        print(f"   System Count: {current_system_count}")
        print(f"   Accuracy: {accuracy:.1f}%")
        print(f"   Notes: {notes}")
        
        self.save_metrics()
        return accuracy
    
    def get_current_system_count(self):
        """Get current count from database."""
        try:
            conn = sqlite3.connect('data/database.db')
            cursor = conn.cursor()
            
            # Get total entries minus exits
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN event_type = 'entry' THEN 1 ELSE 0 END), 0) as entries,
                    COALESCE(SUM(CASE WHEN event_type = 'exit' THEN 1 ELSE 0 END), 0) as exits
                FROM events 
                WHERE timestamp >= ?
            """, (self.start_time.isoformat(),))
            
            result = cursor.fetchone()
            entries, exits = result if result else (0, 0)
            
            conn.close()
            return entries - exits
            
        except Exception as e:
            print(f"Error getting system count: {e}")
            return 0
    
    def get_session_stats(self):
        """Get current session statistics."""
        duration = datetime.now() - self.start_time
        avg_fps = sum(m['fps'] for m in self.metrics['fps_history'][-10:]) / min(10, len(self.metrics['fps_history'])) if self.metrics['fps_history'] else 0
        
        stats = {
            'session_duration': str(duration).split('.')[0],  # Remove microseconds
            'total_detections': self.metrics['total_detections'],
            'total_crossings': self.metrics['total_crossings'],
            'average_fps': round(avg_fps, 1),
            'accuracy_checks': len(self.metrics['manual_counts']),
            'latest_accuracy': self.metrics['accuracy_history'][-1] if self.metrics['accuracy_history'] else None
        }
        
        return stats
    
    def print_session_summary(self):
        """Print session summary."""
        stats = self.get_session_stats()
        
        print("\n" + "="*50)
        print("📊 ACCURACY MONITORING SESSION SUMMARY")
        print("="*50)
        print(f"Session Duration: {stats['session_duration']}")
        print(f"Total Detections: {stats['total_detections']}")
        print(f"Total Crossings: {stats['total_crossings']}")
        print(f"Average FPS: {stats['average_fps']}")
        print(f"Accuracy Checks: {stats['accuracy_checks']}")
        
        if stats['latest_accuracy']:
            print(f"Latest Accuracy: {stats['latest_accuracy']:.1f}%")
        
        if self.metrics['accuracy_history']:
            avg_accuracy = sum(self.metrics['accuracy_history']) / len(self.metrics['accuracy_history'])
            print(f"Average Accuracy: {avg_accuracy:.1f}%")
        
        print("="*50)
    
    def save_metrics(self):
        """Save metrics to file."""
        try:
            Path("data").mkdir(exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics: {e}")
    
    def load_metrics(self):
        """Load metrics from file."""
        try:
            if Path(self.metrics_file).exists():
                with open(self.metrics_file, 'r') as f:
                    self.metrics = json.load(f)
                print("📊 Previous accuracy metrics loaded")
        except Exception as e:
            print(f"Error loading metrics: {e}")


def interactive_accuracy_test():
    """Interactive accuracy testing tool."""
    monitor = AccuracyMonitor()
    monitor.load_metrics()
    
    print("\n🎯 ACCURACY MONITORING TOOL")
    print("="*40)
    print("This tool helps you verify system accuracy")
    print("Commands:")
    print("  'count X' - Record manual count of X people")
    print("  'stats' - Show session statistics")
    print("  'help' - Show this help")
    print("  'quit' - Exit tool")
    print("="*40)
    
    try:
        while True:
            command = input("\n📊 Enter command: ").strip().lower()
            
            if command.startswith('count '):
                try:
                    count = int(command.split()[1])
                    notes = input("📝 Notes (optional): ").strip()
                    accuracy = monitor.add_manual_count(count, notes)
                    
                    if accuracy < 80:
                        print("⚠️  Low accuracy detected! Consider:")
                        print("   - Checking camera positioning")
                        print("   - Improving lighting")
                        print("   - Adjusting detection thresholds")
                        
                except (ValueError, IndexError):
                    print("❌ Invalid format. Use: count X (where X is a number)")
            
            elif command == 'stats':
                monitor.print_session_summary()
            
            elif command == 'help':
                print("\n📋 Commands:")
                print("  count X - Record that you manually counted X people")
                print("  stats   - Show detailed session statistics")
                print("  help    - Show this help message")
                print("  quit    - Exit the accuracy monitoring tool")
            
            elif command == 'quit':
                monitor.save_metrics()
                print("📊 Accuracy metrics saved. Goodbye!")
                break
            
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
    except KeyboardInterrupt:
        monitor.save_metrics()
        print("\n📊 Accuracy monitoring stopped. Metrics saved.")


if __name__ == "__main__":
    interactive_accuracy_test()