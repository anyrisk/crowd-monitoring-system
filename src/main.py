"""Main application for Smart Crowd Monitoring System."""
import sys
import os
import cv2
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import get_config
from utils.logger import default_logger, log_system_event
from src.detector import create_detector
from src.simple_tracker import create_tracker
from src.improved_counter import create_counter
from src.simple_overlay import create_overlay_manager
from src.simple_alerts import create_alert_manager
from src.database import get_database_manager


class CrowdMonitoringSystem:
    """Main crowd monitoring application with real-time video processing."""
    
    def __init__(self, camera_source=None, config_file=None):
        """Initialize the crowd monitoring system."""
        self.config = get_config()
        self.logger = default_logger
        
        # Override camera source if provided
        if camera_source is not None:
            self.config.CAMERA_SOURCE = camera_source
        
        # Initialize components
        self.camera = None
        self.detector = None
        self.tracker = None
        self.counter = None
        self.overlay_manager = None
        self.alert_manager = None
        self.db_manager = None
        
        # Runtime state
        self.running = False
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Initialize all components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components."""
        try:
            log_system_event(self.logger, "Initializing Crowd Monitoring System")
            
            # Initialize database
            self.db_manager = get_database_manager()
            
            # Initialize detector
            self.detector = create_detector()
            
            # Initialize tracker
            self.tracker = create_tracker()
            
            # Initialize counter
            self.counter = create_counter()
            
            # Initialize overlay manager
            self.overlay_manager = create_overlay_manager()
            
            # Initialize alert manager
            self.alert_manager = create_alert_manager()
            
            log_system_event(self.logger, "All components initialized successfully")
            
        except Exception as e:
            log_system_event(self.logger, "Component initialization failed", str(e))
            raise
    
    def _initialize_camera(self):
        """Initialize camera capture."""
        try:
            log_system_event(self.logger, f"Initializing camera: {self.config.CAMERA_SOURCE}")
            
            self.camera = cv2.VideoCapture(self.config.CAMERA_SOURCE)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"Cannot open camera {self.config.CAMERA_SOURCE}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, self.config.FPS)
            
            # Get actual camera properties
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            log_system_event(self.logger, 
                           f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            return True
            
        except Exception as e:
            log_system_event(self.logger, "Camera initialization failed", str(e))
            return False
    
    def _process_frame(self, frame):
        """Process a single frame through the detection pipeline."""
        try:
            # Get frame dimensions
            frame_height, frame_width = frame.shape[:2]
            
            # Detect people in frame
            detections = self.detector.detect_persons(frame)
            
            # Update tracker with detections
            tracked_objects = self.tracker.update(detections)
            
            # Update counter with tracked objects
            crossings = self.counter.update(tracked_objects, frame_width, frame_height)
            
            # Check for alerts
            current_count = self.counter.get_counts()['count_inside']
            self.alert_manager.check_crowd_limit(current_count)
            
            # Create overlay with all information
            overlay_frame = self.overlay_manager.create_overlay(
                frame=frame,
                detections=detections,
                tracked_objects=tracked_objects,
                counts=self.counter.get_counts(),
                crossings=crossings,
                fps=self.current_fps
            )
            
            return overlay_frame
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {e}")
            return frame
    
    def _calculate_fps(self):
        """Calculate current FPS."""
        self.fps_counter += 1
        
        if self.fps_counter >= 30:  # Update FPS every 30 frames
            current_time = time.time()
            elapsed_time = current_time - self.fps_start_time
            
            if elapsed_time > 0:
                self.current_fps = self.fps_counter / elapsed_time
            
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def _handle_keyboard_input(self, key):
        """Handle keyboard input during video processing."""
        if key == ord('q') or key == 27:  # 'q' or ESC
            self.running = False
            return True
        
        elif key == ord('r'):  # Reset counts
            success = self.counter.reset_counts("Manual reset via keyboard")
            if success:
                self.logger.info("Counts reset successfully")
                self.alert_manager.show_info_alert("Counts Reset", "All counts have been reset to zero")
            else:
                self.logger.error("Failed to reset counts")
        
        elif key == ord('s'):  # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.jpg"
            
            # Get current frame
            ret, frame = self.camera.read()
            if ret:
                processed_frame = self._process_frame(frame)
                cv2.imwrite(filename, processed_frame)
                self.logger.info(f"Screenshot saved: {filename}")
                self.alert_manager.show_info_alert("Screenshot Saved", f"Saved as {filename}")
        
        elif key == ord('h'):  # Toggle help
            self.overlay_manager.toggle_help_display()
        
        elif key == ord(' '):  # Spacebar - pause/resume
            self.logger.info("Video paused - press any key to continue")
            cv2.waitKey(0)
        
        return False
    
    def run(self):
        """Main application loop."""
        try:
            log_system_event(self.logger, "Starting Crowd Monitoring System")
            
            # Initialize camera
            if not self._initialize_camera():
                self.logger.error("Failed to initialize camera")
                return False
            
            # Create window with close button functionality
            window_name = "Crowd Monitoring System"
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            
            # Enable window close button
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
            
            # Display startup message
            print("\n" + "="*60)
            print("CROWD MONITORING SYSTEM STARTED")
            print("="*60)
            print("Camera:", self.config.CAMERA_SOURCE)
            print("Controls:")
            print("   'q' - Quit application")
            print("   'r' - Reset all counts")
            print("   's' - Save screenshot")
            print("   'h' - Toggle help display")
            print("   'SPACE' - Pause/Resume")
            print("   'X' button - Close window")
            print("="*60)
            
            self.running = True
            self.fps_start_time = time.time()
            
            # Main processing loop
            while self.running:
                ret, frame = self.camera.read()
                
                if not ret:
                    self.logger.error("Failed to read frame from camera")
                    break
                
                self.frame_count += 1
                
                # Process frame
                processed_frame = self._process_frame(frame)
                
                # Calculate FPS
                self._calculate_fps()
                
                # Display frame
                cv2.imshow(window_name, processed_frame)
                
                # Handle keyboard input and window close button
                key = cv2.waitKey(1) & 0xFF
                
                # Check if window was closed
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
                    break
                
                if key != 255:  # Key was pressed
                    if self._handle_keyboard_input(key):
                        break
            
            log_system_event(self.logger, "Crowd Monitoring System stopped")
            return True
            
        except KeyboardInterrupt:
            log_system_event(self.logger, "System stopped by user (Ctrl+C)")
            return True
            
        except Exception as e:
            log_system_event(self.logger, "System error", str(e))
            self.logger.error(f"System error: {e}")
            return False
            
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.camera:
                self.camera.release()
            
            cv2.destroyAllWindows()
            
            # Brief shutdown message
            print("\nSystem shutdown complete.")
            
            log_system_event(self.logger, "System cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def get_status(self):
        """Get current system status."""
        if not self.running:
            return {"status": "stopped"}
        
        counts = self.counter.get_counts() if self.counter else {}
        
        return {
            "status": "running",
            "frame_count": self.frame_count,
            "fps": self.current_fps,
            "counts": counts,
            "camera_source": self.config.CAMERA_SOURCE
        }


def create_crowd_monitor(camera_source=None, config_file=None):
    """Factory function to create a CrowdMonitoringSystem instance."""
    return CrowdMonitoringSystem(camera_source=camera_source, config_file=config_file)


def main():
    """Main entry point."""
    try:
        app = CrowdMonitoringSystem()
        success = app.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
