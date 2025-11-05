"""
Simple alert manager for the Crowd Monitoring System.
Basic alert functionality for demonstration purposes.
"""

import time
from datetime import datetime
from typing import Optional


class SimpleAlertManager:
    """Simple alert manager with basic functionality."""
    
    def __init__(self):
        """Initialize the alert manager."""
        self.crowd_limit = 100  # Default limit
        self.warning_threshold = 80  # 80% of limit
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds
        self.current_alert = None
    
    def check_crowd_limit(self, current_count):
        """Check if crowd limit alerts should be triggered."""
        current_time = time.time()
        
        # Check if enough time has passed since last alert
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        if current_count >= self.crowd_limit:
            self._trigger_alert("CROWD LIMIT EXCEEDED", 
                              f"Current count: {current_count}, Limit: {self.crowd_limit}")
            self.last_alert_time = current_time
            
        elif current_count >= self.warning_threshold:
            self._trigger_alert("CROWD WARNING", 
                              f"Current count: {current_count}, Warning at: {self.warning_threshold}")
            self.last_alert_time = current_time
    
    def _trigger_alert(self, alert_type, message):
        """Trigger an alert."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🚨 ALERT [{timestamp}]: {alert_type}")
        print(f"   {message}")
        
        self.current_alert = {
            'type': alert_type,
            'message': message,
            'timestamp': timestamp
        }
    
    def show_info_alert(self, title, message):
        """Show an informational alert."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\nℹ️  INFO [{timestamp}]: {title}")
        print(f"   {message}")
    
    def get_current_alert(self):
        """Get current alert if any."""
        return self.current_alert
    
    def clear_alert(self):
        """Clear current alert."""
        self.current_alert = None


def create_alert_manager():
    """Factory function to create alert manager."""
    return SimpleAlertManager()