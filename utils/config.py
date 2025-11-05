"""
Configuration management for the Smart Crowd Monitoring System.
Handles all application settings including camera, detection, counting, and alert parameters.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class for all application settings."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize configuration with default values and optional config file.
        
        Args:
            config_file (str): Path to JSON configuration file (optional)
        """
        self.config_file = config_file
        self._load_defaults()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def _load_defaults(self):
        """Load default configuration values."""
        # Project paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.MODELS_DIR = self.PROJECT_ROOT / "models"
        self.REPORTS_DIR = self.DATA_DIR / "reports"
        
        # Database settings
        self.DATABASE_PATH = str(self.DATA_DIR / "database.db")
        
        # Camera settings
        self.CAMERA_SOURCE = int(os.getenv("CAMERA_SOURCE", 0))
        self.FRAME_WIDTH = 1280
        self.FRAME_HEIGHT = 720
        self.FPS = 30
        
        # YOLO Detection settings
        self.YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov5s.pt")
        self.CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
        self.NMS_THRESHOLD = float(os.getenv("NMS_THRESHOLD", 0.4))
        self.DEVICE = "cpu"  # Can be "cuda" if GPU available
        
        # Tracking settings
        self.MAX_DISAPPEARED = 30  # Frames before object is considered gone
        self.MAX_DISTANCE = 100    # Max distance for object association
        
        # Counting line settings (as percentage of frame dimensions)
        self.COUNTING_LINE = {
            "start": (0.3, 0.5),  # (x%, y%) - left side of line
            "end": (0.7, 0.5),    # (x%, y%) - right side of line
            "thickness": 3,
            "color": (0, 255, 0)  # Green line
        }
        
        # Direction settings (Right to Left = Entry, Left to Right = Exit)
        self.ENTRY_DIRECTION = "right_to_left"  # "right_to_left" or "left_to_right"
        self.EXIT_DIRECTION = "left_to_right"   # Opposite of entry
        
        # Crowd management
        self.CROWD_LIMIT = int(os.getenv("CROWD_LIMIT", 100))
        self.WARNING_THRESHOLD = int(self.CROWD_LIMIT * 0.8)  # 80% of limit
        
        # Alert settings
        self.ALERT_ENABLED = os.getenv("ALERT_ENABLED", "True").lower() == "true"
        self.SOUND_ALERTS = True
        self.POPUP_ALERTS = True
        self.ALERT_COOLDOWN = 30  # Seconds between alerts
        
        # Web dashboard settings
        self.FLASK_HOST = os.getenv('FLASK_HOST', 'localhost')
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        # Display settings
        self.SHOW_BOUNDING_BOXES = True
        self.SHOW_TRACKING_IDS = True
        self.SHOW_COUNTING_LINE = False  # Hide counting line
        self.SHOW_STATISTICS = True
        
        # Colors (BGR format for OpenCV)
        self.COLORS = {
            "person_box": (255, 0, 0),      # Blue
            "tracking_id": (0, 255, 255),   # Yellow
            "counting_line": (0, 255, 0),   # Green
            "entry_point": (0, 255, 0),     # Green
            "exit_point": (0, 0, 255),      # Red
            "text_background": (0, 0, 0),   # Black
            "text_color": (255, 255, 255)   # White
        }
        
        # Font settings
        self.FONT_SCALE = 0.7
        self.FONT_THICKNESS = 2
        
        # Web dashboard settings
        self.FLASK_HOST = os.getenv("FLASK_HOST", "localhost")
        self.FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
        self.DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = "logs/crowd_monitor.log"
        
        # Report settings
        self.AUTO_GENERATE_REPORTS = True
        self.REPORT_FORMATS = ["csv", "xlsx"]
        self.REPORT_SCHEDULE = "daily"  # "hourly", "daily", "weekly"
    
    def get_counting_line_coords(self, frame_width: int, frame_height: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Convert percentage-based line coordinates to pixel coordinates.
        
        Args:
            frame_width (int): Width of video frame
            frame_height (int): Height of video frame
            
        Returns:
            Tuple of start and end coordinates as pixel values
        """
        start_x = int(self.COUNTING_LINE["start"][0] * frame_width)
        start_y = int(self.COUNTING_LINE["start"][1] * frame_height)
        end_x = int(self.COUNTING_LINE["end"][0] * frame_width)
        end_y = int(self.COUNTING_LINE["end"][1] * frame_height)
        
        return ((start_x, start_y), (end_x, end_y))
    
    def load_from_file(self, config_file: str):
        """
        Load configuration from JSON file.
        
        Args:
            config_file (str): Path to JSON configuration file
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            # Update configuration with values from file
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    def save_to_file(self, config_file: str = None):
        """
        Save current configuration to JSON file.
        
        Args:
            config_file (str): Path to save configuration (optional)
        """
        if not config_file:
            config_file = self.config_file or "config.json"
        
        # Create dictionary of all configuration values
        config_data = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                # Convert Path objects to strings for JSON serialization
                if isinstance(value, Path):
                    value = str(value)
                config_data[attr] = value
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=4, default=str)
            print(f"Configuration saved to {config_file}")
        except Exception as e:
            print(f"Error saving config file {config_file}: {e}")
    
    def update_counting_line(self, start_percent: Tuple[float, float], end_percent: Tuple[float, float]):
        """
        Update counting line coordinates.
        
        Args:
            start_percent (Tuple[float, float]): Start coordinates as (x%, y%)
            end_percent (Tuple[float, float]): End coordinates as (x%, y%)
        """
        self.COUNTING_LINE["start"] = start_percent
        self.COUNTING_LINE["end"] = end_percent
    
    def update_crowd_limit(self, new_limit: int):
        """
        Update crowd limit and warning threshold.
        
        Args:
            new_limit (int): New crowd limit
        """
        self.CROWD_LIMIT = new_limit
        self.WARNING_THRESHOLD = int(new_limit * 0.8)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of key configuration values.
        
        Returns:
            Dict containing key configuration parameters
        """
        return {
            "camera_source": self.CAMERA_SOURCE,
            "yolo_model": self.YOLO_MODEL_PATH,
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
            "crowd_limit": self.CROWD_LIMIT,
            "counting_line": self.COUNTING_LINE,
            "alert_enabled": self.ALERT_ENABLED,
            "database_path": self.DATABASE_PATH
        }


# Global configuration instance
config = Config()

# Convenience functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def reload_config(config_file: str = None):
    """Reload configuration from file."""
    global config
    config = Config(config_file)
    return config