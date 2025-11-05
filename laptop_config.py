"""
Laptop Camera Configuration
Optimized settings for built-in laptop cameras
"""

def configure_for_laptop_camera():
    """Configure system for optimal laptop camera performance."""
    
    # Update .env file for laptop camera
    env_content = """# Environment Configuration - Laptop Camera Optimized
# Database
DATABASE_PATH=data/database.db

# Camera Settings (Laptop Camera)
CAMERA_SOURCE=0  # Built-in laptop camera

# Detection Settings (Optimized for closer range)
YOLO_MODEL_PATH=models/yolov5s.pt
CONFIDENCE_THRESHOLD=0.4  # Lower threshold for better detection
NMS_THRESHOLD=0.4

# Crowd Management
CROWD_LIMIT=50  # Reasonable limit for laptop camera range
ALERT_ENABLED=True

# Web Dashboard
FLASK_HOST=localhost
FLASK_PORT=5000
DEBUG_MODE=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/crowd_monitor.log
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Laptop camera configuration applied!")
    print("📹 Camera source set to 0 (built-in laptop camera)")
    print("🎯 Detection threshold lowered for better close-range detection")
    print("👥 Crowd limit set to 50 (appropriate for laptop camera range)")

if __name__ == "__main__":
    configure_for_laptop_camera()