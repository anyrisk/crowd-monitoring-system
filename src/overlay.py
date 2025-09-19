"""
Video overlay module for the Smart Temple People Counter.
Handles drawing all visual elements on video frames including bounding boxes, 
tracking IDs, counting line, statistics, and alerts.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from utils.config import get_config
from utils.draw_utils import (
    draw_bounding_box, draw_tracking_id, draw_trajectory, 
    draw_counting_line, draw_count_display, draw_alert_message, 
    draw_fps_counter, draw_detection_confidence
)
from utils.logger import default_logger
from src.counter import LineCrossing, CrossingDirection


class VideoOverlay:
    """
    Manages all visual overlays for the people counter video feed.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize video overlay manager.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        
        # Display settings
        self.show_bounding_boxes = self.config.SHOW_BOUNDING_BOXES
        self.show_tracking_ids = self.config.SHOW_TRACKING_IDS
        self.show_counting_line = self.config.SHOW_COUNTING_LINE
        self.show_statistics = self.config.SHOW_STATISTICS
        
        # Visual elements state
        self.current_alert = None
        self.alert_start_time = None
        self.fps_history = []
        self.fps_update_interval = 10  # frames
        
        # Crossing visualization
        self.recent_crossings = []
        self.crossing_display_duration = 2.0  # seconds
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw detection bounding boxes on the frame.
        
        Args:
            frame: Input video frame
            detections: List of detection dictionaries
            
        Returns:
            Frame with detection boxes drawn
        """
        if not self.show_bounding_boxes or not detections:
            return frame
        
        for detection in detections:
            bbox = detection.get('bbox')
            confidence = detection.get('confidence')
            
            if bbox:
                # Draw bounding box
                frame = draw_bounding_box(
                    frame, bbox, 
                    color=self.config.COLORS['person_box'],
                    thickness=2,
                    label="Person",
                    confidence=confidence
                )
        
        return frame
    
    def draw_tracking(self, frame: np.ndarray, tracked_objects: Dict[int, Dict]) -> np.ndarray:
        """
        Draw tracking information (IDs and trajectories) on the frame.
        
        Args:
            frame: Input video frame
            tracked_objects: Dictionary of tracked objects
            
        Returns:
            Frame with tracking information drawn
        """
        if not tracked_objects:
            return frame
        
        for object_id, obj_data in tracked_objects.items():
            centroid = obj_data.get('centroid')
            bbox = obj_data.get('bbox')
            history = obj_data.get('history', [])
            
            if centroid:
                # Draw tracking ID
                if self.show_tracking_ids:
                    frame = draw_tracking_id(
                        frame, centroid, object_id,
                        color=self.config.COLORS['tracking_id']
                    )
                
                # Draw trajectory
                if len(history) > 1:
                    # Limit trajectory length for performance
                    recent_history = history[-20:]
                    frame = draw_trajectory(
                        frame, recent_history,
                        color=self.config.COLORS['tracking_id'],
                        thickness=2
                    )
            
            # Update bounding box with tracking color if available
            if bbox and self.show_bounding_boxes:
                frame = draw_bounding_box(
                    frame, bbox,
                    color=self.config.COLORS['person_box'],
                    thickness=2,
                    label=f"ID: {object_id}"
                )
        
        return frame
    
    def draw_counting_line_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw the counting line on the frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            Frame with counting line drawn
        """
        if not self.show_counting_line:
            return frame
        
        height, width = frame.shape[:2]
        line_start, line_end = self.config.get_counting_line_coords(width, height)
        
        frame = draw_counting_line(
            frame, line_start, line_end,
            color=self.config.COLORS['counting_line'],
            thickness=self.config.COUNTING_LINE['thickness'],
            label="Entry/Exit Line"
        )
        
        return frame
    
    def draw_statistics(self, frame: np.ndarray, counts: Dict[str, int], 
                       fps: float = None) -> np.ndarray:
        """
        Draw count statistics and performance metrics on the frame.
        
        Args:
            frame: Input video frame
            counts: Dictionary with count statistics
            fps: Current FPS value
            
        Returns:
            Frame with statistics drawn
        """
        if self.show_statistics:
            # Draw count display
            frame = draw_count_display(frame, counts, position="top_left")
        
        # Draw FPS counter if provided
        if fps is not None:
            frame = draw_fps_counter(frame, fps)
        
        return frame
    
    def draw_crossings(self, frame: np.ndarray, new_crossings: List[LineCrossing]) -> np.ndarray:
        """
        Draw crossing events with visual indicators.
        
        Args:
            frame: Input video frame
            new_crossings: List of new crossing events
            
        Returns:
            Frame with crossing indicators drawn
        """
        current_time = datetime.now()
        
        # Add new crossings to recent list
        for crossing in new_crossings:
            self.recent_crossings.append({
                'crossing': crossing,
                'timestamp': current_time
            })
        
        # Remove old crossings
        self.recent_crossings = [
            item for item in self.recent_crossings
            if (current_time - item['timestamp']).total_seconds() < self.crossing_display_duration
        ]
        
        # Draw recent crossings
        for item in self.recent_crossings:
            crossing = item['crossing']
            elapsed = (current_time - item['timestamp']).total_seconds()
            
            # Fade out effect
            alpha = 1.0 - (elapsed / self.crossing_display_duration)
            
            # Choose color based on direction
            if crossing.direction == CrossingDirection.ENTRY:
                base_color = self.config.COLORS['entry_point']
                label = "ENTRY"
            else:
                base_color = self.config.COLORS['exit_point']
                label = "EXIT"
            
            # Apply fade effect
            color = tuple(int(c * alpha) for c in base_color)
            
            # Draw crossing point
            if crossing.crossing_point:
                x, y = crossing.crossing_point
                
                # Draw circle at crossing point
                radius = int(15 * alpha)
                if radius > 0:
                    cv2.circle(frame, (x, y), radius, color, 3)
                
                # Draw label
                if alpha > 0.5:
                    cv2.putText(frame, label, (x - 30, y - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame
    
    def draw_alert(self, frame: np.ndarray, alert_message: str = None, 
                  alert_type: str = "warning") -> np.ndarray:
        """
        Draw alert messages on the frame.
        
        Args:
            frame: Input video frame
            alert_message: Alert message to display
            alert_type: Type of alert ("warning", "critical", "info")
            
        Returns:
            Frame with alert message drawn
        """
        # Update current alert
        if alert_message:
            self.current_alert = alert_message
            self.alert_start_time = datetime.now()
        
        # Draw current alert if within display time
        if self.current_alert and self.alert_start_time:
            elapsed = (datetime.now() - self.alert_start_time).total_seconds()
            
            # Display alert for 5 seconds
            if elapsed < 5.0:
                frame = draw_alert_message(frame, self.current_alert, alert_type)
            else:
                # Clear expired alert
                self.current_alert = None
                self.alert_start_time = None
        
        return frame
    
    def draw_timestamp(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw current timestamp on the frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            Frame with timestamp drawn
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        height, width = frame.shape[:2]
        
        # Position at bottom right
        (text_width, text_height), baseline = cv2.getTextSize(
            timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        
        x = width - text_width - 10
        y = height - 10
        
        # Draw background
        cv2.rectangle(frame, (x - 5, y - text_height - 5),
                     (x + text_width + 5, y + 5), (0, 0, 0), -1)
        
        # Draw timestamp
        cv2.putText(frame, timestamp, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (255, 255, 255), 2)
        
        return frame
    
    def process_frame(self, frame: np.ndarray, detections: List[Dict], 
                     tracked_objects: Dict[int, Dict], counts: Dict[str, int],
                     crossings: List[LineCrossing] = None, fps: float = None,
                     alert_message: str = None, alert_type: str = "warning") -> np.ndarray:
        """
        Process a frame with all overlay elements.
        
        Args:
            frame: Input video frame
            detections: List of detection dictionaries
            tracked_objects: Dictionary of tracked objects
            counts: Dictionary with count statistics
            crossings: List of new crossing events
            fps: Current FPS value
            alert_message: Alert message to display
            alert_type: Type of alert
            
        Returns:
            Processed frame with all overlays
        """
        # Make a copy to avoid modifying the original frame
        overlay_frame = frame.copy()
        
        # Draw counting line (first, so it appears under other elements)
        overlay_frame = self.draw_counting_line_overlay(overlay_frame)
        
        # Draw detections
        overlay_frame = self.draw_detections(overlay_frame, detections)
        
        # Draw tracking information
        overlay_frame = self.draw_tracking(overlay_frame, tracked_objects)
        
        # Draw crossing events
        if crossings:
            overlay_frame = self.draw_crossings(overlay_frame, crossings)
        
        # Draw statistics
        overlay_frame = self.draw_statistics(overlay_frame, counts, fps)
        
        # Draw alerts
        overlay_frame = self.draw_alert(overlay_frame, alert_message, alert_type)
        
        # Draw timestamp
        overlay_frame = self.draw_timestamp(overlay_frame)
        
        return overlay_frame
    
    def toggle_display_element(self, element: str):
        """
        Toggle display of specific overlay elements.
        
        Args:
            element: Element to toggle ("boxes", "ids", "line", "stats")
        """
        if element == "boxes":
            self.show_bounding_boxes = not self.show_bounding_boxes
            self.logger.info(f"Bounding boxes: {'ON' if self.show_bounding_boxes else 'OFF'}")
        
        elif element == "ids":
            self.show_tracking_ids = not self.show_tracking_ids
            self.logger.info(f"Tracking IDs: {'ON' if self.show_tracking_ids else 'OFF'}")
        
        elif element == "line":
            self.show_counting_line = not self.show_counting_line
            self.logger.info(f"Counting line: {'ON' if self.show_counting_line else 'OFF'}")
        
        elif element == "stats":
            self.show_statistics = not self.show_statistics
            self.logger.info(f"Statistics: {'ON' if self.show_statistics else 'OFF'}")
    
    def get_display_settings(self) -> Dict[str, bool]:
        """
        Get current display settings.
        
        Returns:
            Dictionary with current display settings
        """
        return {
            'show_bounding_boxes': self.show_bounding_boxes,
            'show_tracking_ids': self.show_tracking_ids,
            'show_counting_line': self.show_counting_line,
            'show_statistics': self.show_statistics
        }


def create_overlay() -> VideoOverlay:
    """
    Factory function to create a VideoOverlay instance.
    
    Returns:
        VideoOverlay instance
    """
    return VideoOverlay()