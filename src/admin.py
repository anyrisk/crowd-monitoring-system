"""
Administrative controls for the Smart Temple People Counter.
Provides count reset, configuration management, and system administration features.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json
import os

from utils.config import get_config, reload_config
from utils.logger import default_logger, log_system_event
from src.database import get_database_manager
from src.alerts import create_alert_manager
from src.reports import create_report_generator


class AdminController:
    """
    Handles administrative functions for the people counter system.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize admin controller.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        self.db_manager = get_database_manager()
        self.alert_manager = create_alert_manager()
        self.report_generator = create_report_generator()
        
        # Admin session tracking
        self.session_start = datetime.now()
        self.admin_actions = []
    
    def reset_all_counts(self, reason: str = "Admin reset", admin_user: str = "system") -> Dict[str, Any]:
        """
        Reset all people counts to zero.
        
        Args:
            reason (str): Reason for the reset
            admin_user (str): Name of admin performing the action
            
        Returns:
            Dictionary with reset operation results
        """
        try:
            log_system_event(self.logger, f"Admin reset initiated by {admin_user}", reason)
            
            # Get current counts before reset
            current_counts = self.db_manager.get_current_count()
            
            # Perform reset
            success = self.db_manager.reset_counts(f"{reason} (by {admin_user})")
            
            # Log admin action
            self._log_admin_action("reset_counts", admin_user, {
                "reason": reason,
                "previous_counts": current_counts,
                "success": success
            })
            
            # Clear any active alerts
            if success:
                self.alert_manager.clear_all_alerts()
            
            result = {
                "success": success,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "reason": reason,
                "previous_counts": current_counts,
                "message": "Counts reset successfully" if success else "Failed to reset counts"
            }
            
            log_system_event(self.logger, "Admin reset completed", f"Success: {success}")
            return result
            
        except Exception as e:
            error_msg = f"Error during admin reset: {e}"
            log_system_event(self.logger, "Admin reset failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "reason": reason,
                "error": error_msg,
                "message": "Reset operation failed"
            }
    
    def update_crowd_limit(self, new_limit: int, admin_user: str = "system") -> Dict[str, Any]:
        """
        Update the crowd limit threshold.
        
        Args:
            new_limit (int): New crowd limit value
            admin_user (str): Name of admin performing the action
            
        Returns:
            Dictionary with update operation results
        """
        try:
            if new_limit <= 0:
                raise ValueError("Crowd limit must be greater than 0")
            
            old_limit = self.config.CROWD_LIMIT
            
            # Update configuration
            self.config.update_crowd_limit(new_limit)
            
            # Log admin action
            self._log_admin_action("update_crowd_limit", admin_user, {
                "old_limit": old_limit,
                "new_limit": new_limit
            })
            
            log_system_event(self.logger, f"Crowd limit updated by {admin_user}", 
                           f"From {old_limit} to {new_limit}")
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "old_limit": old_limit,
                "new_limit": new_limit,
                "message": f"Crowd limit updated to {new_limit}"
            }
            
        except Exception as e:
            error_msg = f"Error updating crowd limit: {e}"
            log_system_event(self.logger, "Crowd limit update failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Failed to update crowd limit"
            }
    
    def update_counting_line(self, start_coords: Tuple[float, float], 
                           end_coords: Tuple[float, float], 
                           admin_user: str = "system") -> Dict[str, Any]:
        """
        Update the counting line position.
        
        Args:
            start_coords: Start coordinates as percentage (x%, y%)
            end_coords: End coordinates as percentage (x%, y%)
            admin_user: Name of admin performing the action
            
        Returns:
            Dictionary with update operation results
        """
        try:
            # Validate coordinates
            for coord in start_coords + end_coords:
                if not (0.0 <= coord <= 1.0):
                    raise ValueError("Coordinates must be between 0.0 and 1.0")
            
            old_line = self.config.COUNTING_LINE.copy()
            
            # Update configuration
            self.config.update_counting_line(start_coords, end_coords)
            
            # Log admin action
            self._log_admin_action("update_counting_line", admin_user, {
                "old_line": old_line,
                "new_start": start_coords,
                "new_end": end_coords
            })
            
            log_system_event(self.logger, f"Counting line updated by {admin_user}", 
                           f"Start: {start_coords}, End: {end_coords}")
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "old_line": old_line,
                "new_line": self.config.COUNTING_LINE,
                "message": "Counting line position updated"
            }
            
        except Exception as e:
            error_msg = f"Error updating counting line: {e}"
            log_system_event(self.logger, "Counting line update failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Failed to update counting line"
            }
    
    def update_alert_settings(self, alerts_enabled: bool = None, 
                            sound_alerts: bool = None, popup_alerts: bool = None,
                            alert_cooldown: int = None, admin_user: str = "system") -> Dict[str, Any]:
        """
        Update alert system settings.
        
        Args:
            alerts_enabled: Enable/disable all alerts
            sound_alerts: Enable/disable sound alerts
            popup_alerts: Enable/disable popup alerts
            alert_cooldown: Cooldown period between alerts
            admin_user: Name of admin performing the action
            
        Returns:
            Dictionary with update operation results
        """
        try:
            old_settings = {
                "alerts_enabled": self.config.ALERT_ENABLED,
                "sound_alerts": self.config.SOUND_ALERTS,
                "popup_alerts": self.config.POPUP_ALERTS,
                "alert_cooldown": self.config.ALERT_COOLDOWN
            }
            
            # Update alert manager settings
            self.alert_manager.update_settings(
                alerts_enabled=alerts_enabled,
                sound_alerts=sound_alerts,
                popup_alerts=popup_alerts,
                alert_cooldown=alert_cooldown
            )
            
            # Update configuration
            if alerts_enabled is not None:
                self.config.ALERT_ENABLED = alerts_enabled
            if sound_alerts is not None:
                self.config.SOUND_ALERTS = sound_alerts
            if popup_alerts is not None:
                self.config.POPUP_ALERTS = popup_alerts
            if alert_cooldown is not None:
                self.config.ALERT_COOLDOWN = alert_cooldown
            
            new_settings = {
                "alerts_enabled": self.config.ALERT_ENABLED,
                "sound_alerts": self.config.SOUND_ALERTS,
                "popup_alerts": self.config.POPUP_ALERTS,
                "alert_cooldown": self.config.ALERT_COOLDOWN
            }
            
            # Log admin action
            self._log_admin_action("update_alert_settings", admin_user, {
                "old_settings": old_settings,
                "new_settings": new_settings
            })
            
            log_system_event(self.logger, f"Alert settings updated by {admin_user}")
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "old_settings": old_settings,
                "new_settings": new_settings,
                "message": "Alert settings updated successfully"
            }
            
        except Exception as e:
            error_msg = f"Error updating alert settings: {e}"
            log_system_event(self.logger, "Alert settings update failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Failed to update alert settings"
            }
    
    def generate_system_report(self, report_type: str = "daily", 
                             target_date: date = None, 
                             admin_user: str = "system") -> Dict[str, Any]:
        """
        Generate system reports on demand.
        
        Args:
            report_type: Type of report ("daily", "weekly", "monthly")
            target_date: Target date for report generation
            admin_user: Name of admin performing the action
            
        Returns:
            Dictionary with report generation results
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            log_system_event(self.logger, f"Report generation initiated by {admin_user}", 
                           f"Type: {report_type}, Date: {target_date}")
            
            # Generate report based on type
            if report_type == "daily":
                report_data = self.report_generator.generate_daily_report(target_date)
            elif report_type == "weekly":
                report_data = self.report_generator.generate_weekly_report(target_date)
            elif report_type == "monthly":
                report_data = self.report_generator.generate_monthly_report(
                    target_date.year, target_date.month
                )
            else:
                raise ValueError(f"Invalid report type: {report_type}")
            
            # Export reports
            csv_file = ""
            excel_file = ""
            chart_files = []
            
            if report_data:
                csv_file = self.report_generator.export_to_csv(report_data)
                excel_file = self.report_generator.export_to_excel(report_data)
                chart_files = self.report_generator.generate_charts(report_data)
            
            # Log admin action
            self._log_admin_action("generate_report", admin_user, {
                "report_type": report_type,
                "target_date": str(target_date),
                "files_generated": {
                    "csv": csv_file,
                    "excel": excel_file,
                    "charts": chart_files
                }
            })
            
            result = {
                "success": bool(report_data),
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "report_type": report_type,
                "target_date": target_date,
                "report_data": report_data,
                "files": {
                    "csv": csv_file,
                    "excel": excel_file,
                    "charts": chart_files
                },
                "message": f"{report_type.title()} report generated successfully" if report_data 
                          else "Report generation failed"
            }
            
            log_system_event(self.logger, "Report generation completed", 
                           f"Success: {bool(report_data)}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating report: {e}"
            log_system_event(self.logger, "Report generation failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Report generation failed"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status information.
        
        Returns:
            Dictionary with system status data
        """
        try:
            # Get current counts
            current_counts = self.db_manager.get_current_count()
            
            # Get today's statistics
            today_stats = self.db_manager.get_daily_stats(date.today())
            
            # Get alert statistics
            alert_stats = self.alert_manager.get_alert_statistics()
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            # System configuration summary
            config_summary = self.config.get_summary()
            
            # Admin session info
            session_duration = (datetime.now() - self.session_start).total_seconds() / 60  # minutes
            
            status = {
                "timestamp": datetime.now(),
                "system_uptime_minutes": session_duration,
                "current_counts": current_counts,
                "today_statistics": today_stats,
                "alert_system": {
                    "statistics": alert_stats,
                    "active_alerts_count": len(active_alerts),
                    "active_alerts": [
                        {
                            "type": alert.alert_type.value,
                            "message": alert.message,
                            "timestamp": alert.timestamp
                        } for alert in active_alerts
                    ]
                },
                "configuration": config_summary,
                "admin_actions_count": len(self.admin_actions),
                "database_status": "connected",  # Could add actual health check
                "system_health": "operational"   # Could add comprehensive health check
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "timestamp": datetime.now(),
                "error": str(e),
                "system_health": "error"
            }
    
    def backup_database(self, backup_path: str = None, admin_user: str = "system") -> Dict[str, Any]:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file
            admin_user: Name of admin performing the action
            
        Returns:
            Dictionary with backup operation results
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config.DATA_DIR}/backup_database_{timestamp}.db"
            
            # Simple file copy backup
            import shutil
            shutil.copy2(self.config.DATABASE_PATH, backup_path)
            
            # Log admin action
            self._log_admin_action("backup_database", admin_user, {
                "backup_path": backup_path
            })
            
            log_system_event(self.logger, f"Database backup created by {admin_user}", backup_path)
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "backup_path": backup_path,
                "message": "Database backup created successfully"
            }
            
        except Exception as e:
            error_msg = f"Error creating database backup: {e}"
            log_system_event(self.logger, "Database backup failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Database backup failed"
            }
    
    def save_configuration(self, config_path: str = None, 
                          admin_user: str = "system") -> Dict[str, Any]:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration file
            admin_user: Name of admin performing the action
            
        Returns:
            Dictionary with save operation results
        """
        try:
            if config_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config_path = f"config_backup_{timestamp}.json"
            
            self.config.save_to_file(config_path)
            
            # Log admin action
            self._log_admin_action("save_configuration", admin_user, {
                "config_path": config_path
            })
            
            log_system_event(self.logger, f"Configuration saved by {admin_user}", config_path)
            
            return {
                "success": True,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "config_path": config_path,
                "message": "Configuration saved successfully"
            }
            
        except Exception as e:
            error_msg = f"Error saving configuration: {e}"
            log_system_event(self.logger, "Configuration save failed", str(e))
            
            return {
                "success": False,
                "timestamp": datetime.now(),
                "admin_user": admin_user,
                "error": error_msg,
                "message": "Configuration save failed"
            }
    
    def get_admin_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get audit log of admin actions.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of admin action records
        """
        return self.admin_actions[-limit:] if self.admin_actions else []
    
    def _log_admin_action(self, action: str, admin_user: str, details: Dict[str, Any]):
        """
        Log an administrative action for audit purposes.
        
        Args:
            action: Type of admin action
            admin_user: Name of admin user
            details: Additional action details
        """
        action_record = {
            "timestamp": datetime.now(),
            "action": action,
            "admin_user": admin_user,
            "details": details
        }
        
        self.admin_actions.append(action_record)
        
        # Keep only last 200 actions to prevent memory issues
        if len(self.admin_actions) > 200:
            self.admin_actions = self.admin_actions[-100:]
        
        # Also log to system logger
        log_system_event(self.logger, f"Admin action: {action}", 
                        f"User: {admin_user}, Details: {json.dumps(details, default=str)}")


def create_admin_controller() -> AdminController:
    """
    Factory function to create an AdminController instance.
    
    Returns:
        AdminController instance
    """
    return AdminController()