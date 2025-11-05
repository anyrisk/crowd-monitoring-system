"""
Alert system for the Smart Crowd Monitoring System.
Handles crowd limit notifications, safety alerts, and various notification methods.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
from enum import Enum
import os
import platform

from utils.config import get_config
from utils.logger import default_logger, log_alert
from src.database import get_database_manager


class AlertType(Enum):
    """Types of alerts supported by the system."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    CROWD_WARNING = "crowd_warning"
    CROWD_LIMIT = "crowd_limit"
    SYSTEM_ERROR = "system_error"


class AlertMethod(Enum):
    """Methods for delivering alerts."""
    POPUP = "popup"
    SOUND = "sound"
    LOG = "log"
    DATABASE = "database"
    OVERLAY = "overlay"


class Alert:
    """Represents an alert event."""
    
    def __init__(self, alert_type: AlertType, message: str, 
                 current_count: int = None, threshold: int = None,
                 methods: List[AlertMethod] = None):
        self.alert_type = alert_type
        self.message = message
        self.current_count = current_count
        self.threshold = threshold
        self.timestamp = datetime.now()
        self.methods = methods or [AlertMethod.LOG, AlertMethod.OVERLAY]
        self.resolved = False
        self.resolved_timestamp = None


class AlertManager:
    """
    Manages all alert functionality for the people counter system.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize alert manager.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        self.db_manager = get_database_manager()
        
        # Alert settings
        self.alerts_enabled = self.config.ALERT_ENABLED
        self.sound_alerts = self.config.SOUND_ALERTS
        self.popup_alerts = self.config.POPUP_ALERTS
        self.alert_cooldown = self.config.ALERT_COOLDOWN  # seconds
        
        # Alert state
        self.active_alerts = []
        self.alert_history = []
        self.last_alert_times = {}  # {alert_type: timestamp}
        self.alert_callbacks = {}  # {alert_type: [callback_functions]}
        
        # Threading for non-blocking alerts
        self.alert_thread_pool = []
        
        # Load platform-specific notification modules
        self._load_notification_modules()
    
    def _load_notification_modules(self):
        """Load platform-specific notification modules."""
        try:
            # Try to import notification libraries
            if platform.system() == "Windows":
                try:
                    import winsound
                    self.winsound = winsound
                    self.sound_available = True
                except ImportError:
                    self.sound_available = False
            
            # Cross-platform notifications
            try:
                import plyer
                from plyer import notification
                self.plyer_notification = notification
                self.notification_available = True
            except ImportError:
                self.plyer_notification = None
                self.notification_available = False
                self.logger.warning("Plyer not available - popup notifications disabled")
            
            # Sound alerts with pygame
            try:
                import pygame
                pygame.mixer.init()
                self.pygame = pygame
                self.pygame_sound_available = True
            except ImportError:
                self.pygame_sound_available = False
        
        except Exception as e:
            self.logger.error(f"Error loading notification modules: {e}")
    
    def check_crowd_limits(self, current_count: int) -> List[Alert]:
        """
        Check if current count exceeds configured limits.
        
        Args:
            current_count (int): Current number of people inside
            
        Returns:
            List of alerts generated
        """
        alerts = []
        
        if not self.alerts_enabled:
            return alerts
        
        # Check warning threshold
        if current_count >= self.config.WARNING_THRESHOLD:
            if not self._is_in_cooldown(AlertType.CROWD_WARNING):
                alert = Alert(
                    alert_type=AlertType.CROWD_WARNING,
                    message=f"Approaching capacity limit: {current_count}/{self.config.CROWD_LIMIT}",
                    current_count=current_count,
                    threshold=self.config.WARNING_THRESHOLD,
                    methods=[AlertMethod.LOG, AlertMethod.OVERLAY, AlertMethod.DATABASE]
                )
                alerts.append(alert)
        
        # Check critical limit
        if current_count >= self.config.CROWD_LIMIT:
            if not self._is_in_cooldown(AlertType.CROWD_LIMIT):
                alert = Alert(
                    alert_type=AlertType.CROWD_LIMIT,
                    message=f"CROWD LIMIT EXCEEDED: {current_count}/{self.config.CROWD_LIMIT}",
                    current_count=current_count,
                    threshold=self.config.CROWD_LIMIT,
                    methods=[AlertMethod.POPUP, AlertMethod.SOUND, AlertMethod.LOG, 
                            AlertMethod.OVERLAY, AlertMethod.DATABASE]
                )
                alerts.append(alert)
        
        # Process alerts
        for alert in alerts:
            self.trigger_alert(alert)
        
        return alerts
    
    def trigger_alert(self, alert: Alert):
        """
        Trigger an alert using specified methods.
        
        Args:
            alert (Alert): Alert object to process
        """
        try:
            # Add to active alerts
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            
            # Update last alert time
            self.last_alert_times[alert.alert_type] = alert.timestamp
            
            # Process each alert method
            for method in alert.methods:
                self._process_alert_method(alert, method)
            
            # Execute registered callbacks
            if alert.alert_type in self.alert_callbacks:
                for callback in self.alert_callbacks[alert.alert_type]:
                    try:
                        callback(alert)
                    except Exception as e:
                        self.logger.error(f"Error in alert callback: {e}")
            
            # Clean up old alerts
            self._cleanup_old_alerts()
        
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
    
    def _process_alert_method(self, alert: Alert, method: AlertMethod):
        """
        Process a specific alert method.
        
        Args:
            alert (Alert): Alert object
            method (AlertMethod): Alert method to use
        """
        try:
            if method == AlertMethod.LOG:
                log_alert(self.logger, alert.alert_type.value, 
                         alert.current_count or 0, alert.threshold or 0)
            
            elif method == AlertMethod.DATABASE:
                self.db_manager.log_alert(
                    alert_type=alert.alert_type.value,
                    current_count=alert.current_count or 0,
                    threshold=alert.threshold or 0,
                    notes=alert.message
                )
            
            elif method == AlertMethod.POPUP:
                if self.popup_alerts:
                    self._show_popup_notification(alert)
            
            elif method == AlertMethod.SOUND:
                if self.sound_alerts:
                    self._play_sound_alert(alert)
            
            elif method == AlertMethod.OVERLAY:
                # Overlay alerts are handled by the video overlay system
                pass
        
        except Exception as e:
            self.logger.error(f"Error processing alert method {method}: {e}")
    
    def _show_popup_notification(self, alert: Alert):
        """
        Show popup notification (non-blocking).
        
        Args:
            alert (Alert): Alert object
        """
        def show_notification():
            try:
                if self.notification_available:
                    # Use plyer for cross-platform notifications
                    title = f"Crowd Monitor - {alert.alert_type.value.title()}"
                    
                    self.plyer_notification.notify(
                        title=title,
                        message=alert.message,
                        timeout=10,
                        toast=True
                    )
                else:
                    # Fallback to simple print/log
                    self.logger.info(f"POPUP ALERT: {alert.message}")
            
            except Exception as e:
                self.logger.error(f"Error showing popup notification: {e}")
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=show_notification)
        thread.daemon = True
        thread.start()
        self.alert_thread_pool.append(thread)
    
    def _play_sound_alert(self, alert: Alert):
        """
        Play sound alert (non-blocking).
        
        Args:
            alert (Alert): Alert object
        """
        def play_sound():
            try:
                if alert.alert_type == AlertType.CROWD_LIMIT:
                    # Critical alert sound
                    self._play_critical_sound()
                elif alert.alert_type == AlertType.CROWD_WARNING:
                    # Warning alert sound
                    self._play_warning_sound()
                else:
                    # Default alert sound
                    self._play_default_sound()
            
            except Exception as e:
                self.logger.error(f"Error playing sound alert: {e}")
        
        # Run in separate thread
        thread = threading.Thread(target=play_sound)
        thread.daemon = True
        thread.start()
        self.alert_thread_pool.append(thread)
    
    def _play_critical_sound(self):
        """Play critical alert sound."""
        if platform.system() == "Windows" and self.sound_available:
            # Use Windows system sounds
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        elif self.pygame_sound_available:
            # Use pygame to play custom sound
            # Could load custom alert sound files here
            pass
        else:
            # Fallback - system beep
            if platform.system() == "Windows":
                import winsound
                for _ in range(3):
                    winsound.Beep(1000, 500)
                    time.sleep(0.1)
    
    def _play_warning_sound(self):
        """Play warning alert sound."""
        if platform.system() == "Windows" and self.sound_available:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        else:
            # Fallback - single beep
            if platform.system() == "Windows":
                import winsound
                winsound.Beep(800, 300)
    
    def _play_default_sound(self):
        """Play default alert sound."""
        if platform.system() == "Windows" and self.sound_available:
            import winsound
            winsound.PlaySound("SystemDefault", winsound.SND_ALIAS)
    
    def _is_in_cooldown(self, alert_type: AlertType) -> bool:
        """
        Check if alert type is in cooldown period.
        
        Args:
            alert_type (AlertType): Type of alert to check
            
        Returns:
            True if in cooldown, False otherwise
        """
        if alert_type not in self.last_alert_times:
            return False
        
        last_alert = self.last_alert_times[alert_type]
        elapsed = (datetime.now() - last_alert).total_seconds()
        
        return elapsed < self.alert_cooldown
    
    def _cleanup_old_alerts(self):
        """Remove old alerts from active list."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=5)  # Keep alerts for 5 minutes
        
        # Remove old active alerts
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp > cutoff_time
        ]
        
        # Limit history size
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-50:]
        
        # Clean up finished threads
        self.alert_thread_pool = [
            thread for thread in self.alert_thread_pool
            if thread.is_alive()
        ]
    
    def register_callback(self, alert_type: AlertType, callback: Callable):
        """
        Register a callback function for specific alert types.
        
        Args:
            alert_type (AlertType): Type of alert to listen for
            callback (Callable): Function to call when alert occurs
        """
        if alert_type not in self.alert_callbacks:
            self.alert_callbacks[alert_type] = []
        
        self.alert_callbacks[alert_type].append(callback)
        self.logger.info(f"Registered callback for alert type: {alert_type}")
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get currently active alerts.
        
        Returns:
            List of active alerts
        """
        return self.active_alerts.copy()
    
    def get_latest_overlay_alert(self) -> Optional[Alert]:
        """
        Get the latest alert for overlay display.
        
        Returns:
            Most recent alert suitable for overlay, or None
        """
        overlay_alerts = [
            alert for alert in self.active_alerts
            if AlertMethod.OVERLAY in alert.methods and not alert.resolved
        ]
        
        if overlay_alerts:
            return max(overlay_alerts, key=lambda x: x.timestamp)
        
        return None
    
    def resolve_alert(self, alert: Alert):
        """
        Mark an alert as resolved.
        
        Args:
            alert (Alert): Alert to resolve
        """
        alert.resolved = True
        alert.resolved_timestamp = datetime.now()
        
        # Remove from active alerts
        if alert in self.active_alerts:
            self.active_alerts.remove(alert)
    
    def clear_all_alerts(self):
        """Clear all active alerts."""
        for alert in self.active_alerts:
            alert.resolved = True
            alert.resolved_timestamp = datetime.now()
        
        self.active_alerts.clear()
        self.logger.info("All alerts cleared")
    
    def update_settings(self, alerts_enabled: bool = None, sound_alerts: bool = None,
                       popup_alerts: bool = None, alert_cooldown: int = None):
        """
        Update alert settings.
        
        Args:
            alerts_enabled: Enable/disable all alerts
            sound_alerts: Enable/disable sound alerts
            popup_alerts: Enable/disable popup alerts
            alert_cooldown: Cooldown period between alerts
        """
        if alerts_enabled is not None:
            self.alerts_enabled = alerts_enabled
            self.logger.info(f"Alerts enabled: {alerts_enabled}")
        
        if sound_alerts is not None:
            self.sound_alerts = sound_alerts
            self.logger.info(f"Sound alerts enabled: {sound_alerts}")
        
        if popup_alerts is not None:
            self.popup_alerts = popup_alerts
            self.logger.info(f"Popup alerts enabled: {popup_alerts}")
        
        if alert_cooldown is not None:
            self.alert_cooldown = alert_cooldown
            self.logger.info(f"Alert cooldown set to: {alert_cooldown} seconds")
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get alert system statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        
        # Count by type
        alert_counts = {}
        for alert in self.alert_history:
            alert_type = alert.alert_type.value
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'alert_counts': alert_counts,
            'alerts_enabled': self.alerts_enabled,
            'sound_enabled': self.sound_alerts,
            'popup_enabled': self.popup_alerts,
            'cooldown_period': self.alert_cooldown
        }


def create_alert_manager() -> AlertManager:
    """
    Factory function to create an AlertManager instance.
    
    Returns:
        AlertManager instance
    """
    return AlertManager()