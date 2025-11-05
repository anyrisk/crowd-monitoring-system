"""
Logging utilities for the Smart Crowd Monitoring System.
Provides consistent logging across all modules with different log levels and outputs.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str = "crowd_monitor",
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str): Logger name
        log_file (str, optional): Path to log file
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output (bool): Whether to output to console
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (max 10MB, keep 5 backup files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_detection_event(logger: logging.Logger, event_type: str, person_id: int, count: int):
    """
    Log a detection event (entry/exit).
    
    Args:
        logger: Logger instance
        event_type (str): Type of event ('entry' or 'exit')
        person_id (int): ID of the person
        count (int): Current count after event
    """
    logger.info(f"Detection Event - Type: {event_type}, Person ID: {person_id}, New Count: {count}")


def log_alert(logger: logging.Logger, alert_type: str, current_count: int, limit: int):
    """
    Log an alert event.
    
    Args:
        logger: Logger instance
        alert_type (str): Type of alert ('warning' or 'limit_exceeded')
        current_count (int): Current people count
        limit (int): The limit that triggered the alert
    """
    logger.warning(f"Alert Triggered - Type: {alert_type}, Count: {current_count}, Limit: {limit}")


def log_system_event(logger: logging.Logger, event: str, details: str = ""):
    """
    Log a system event (startup, shutdown, error, etc.).
    
    Args:
        logger: Logger instance
        event (str): Event description
        details (str): Additional details
    """
    if details:
        logger.info(f"System Event - {event}: {details}")
    else:
        logger.info(f"System Event - {event}")


def log_database_operation(logger: logging.Logger, operation: str, success: bool, error: str = ""):
    """
    Log database operations.
    
    Args:
        logger: Logger instance
        operation (str): Database operation description
        success (bool): Whether operation was successful
        error (str): Error message if operation failed
    """
    if success:
        logger.debug(f"Database Operation - {operation}: SUCCESS")
    else:
        logger.error(f"Database Operation - {operation}: FAILED - {error}")


# Create default logger instance
default_logger = setup_logger(
    name="crowd_monitor",
    log_file="logs/crowd_monitor.log",
    log_level="INFO",
    console_output=True
)