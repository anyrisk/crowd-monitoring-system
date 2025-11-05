"""
Simple overlay manager for the Crowd Monitoring System.
Provides basic visual overlays for testing and demonstration.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional


class SimpleOverlayManager:
    """Simple overlay manager with basic functionality."""
    
    def __init__(self):
        """Initialize the overlay manager."""
        self.show_help = False
        self.colors = {
            'person_box': (0, 255, 0),      # Green
            'counting_line': (0, 255, 255), # Yellow
            'text': (255, 255, 255),        # White
            'background': (0, 0, 0),        # Black
            'entry': (0, 255, 0),           # Green
            'exit': (0, 0, 255)             # Red
        }
    
    def create_overlay(self, frame, detections=None, tracked_objects=None, 
                      counts=None, crossings=None, fps=0):
        """Create overlay on frame with all visual elements."""
        overlay_frame = frame.copy()
        
        # Draw detections
        if detections:
            self._draw_detections(overlay_frame, detections)
        
        # Draw counting line (only if enabled in config)
        from utils.config import get_config
        config = get_config()
        if config.SHOW_COUNTING_LINE:
            self._draw_counting_line(overlay_frame)
        
        # Draw statistics - ALWAYS draw them
        self._draw_statistics(overlay_frame, counts or {}, fps, detections, tracked_objects)
        
        # Draw crossings
        if crossings:
            self._draw_crossings(overlay_frame, crossings)
        
        # Draw help if enabled
        if self.show_help:
            self._draw_help(overlay_frame)
        
        return overlay_frame
    
    def _draw_detections(self, frame, detections):
        """Draw bounding boxes around detected people."""
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), 
                         self.colors['person_box'], 2)
            
            # Draw confidence
            label = f"Person {confidence:.2f}"
            cv2.putText(frame, label, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['text'], 2)
    
    def _draw_counting_line(self, frame):
        """Draw the counting line."""
        height, width = frame.shape[:2]
        
        # Default line across middle of frame
        start_point = (int(width * 0.3), int(height * 0.5))
        end_point = (int(width * 0.7), int(height * 0.5))
        
        # Draw line
        cv2.line(frame, start_point, end_point, self.colors['counting_line'], 3)
        
        # Draw line label
        cv2.putText(frame, "COUNTING LINE", (start_point[0], start_point[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.colors['counting_line'], 2)
    
    def _draw_statistics(self, frame, counts, fps, detections=None, tracked_objects=None):
        """Draw statistics overlay."""
        height, width = frame.shape[:2]
        
        # Simple statistics text without special characters
        stats = [
            f"People Inside: {counts.get('count_inside', 0)}",
            f"Total Entries: {counts.get('total_entered', 0)} (R->L)",
            f"Total Exits: {counts.get('total_exited', 0)} (L->R)",
            f"FPS: {fps:.1f}",
            f"Time: {datetime.now().strftime('%H:%M:%S')}",
            f"Detections: {len(detections) if detections else 0}",
            f"Tracked: {len(tracked_objects) if tracked_objects else 0}"
        ]
        
        # Draw background rectangle
        bg_height = len(stats) * 25 + 20
        bg_width = 400
        cv2.rectangle(frame, (10, 10), (bg_width, bg_height), (0, 0, 0), -1)  # Black background
        cv2.rectangle(frame, (10, 10), (bg_width, bg_height), (255, 255, 255), 2)  # White border
        
        # Draw statistics text
        for i, stat in enumerate(stats):
            y_pos = 30 + i * 25
            cv2.putText(frame, stat, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, (255, 255, 255), 2)  # White text
        
        # Draw center reference line (very subtle)
        zone_center_x = int(width * 0.5)
        cv2.line(frame, (zone_center_x, 0), (zone_center_x, height), (128, 128, 128), 1)
    
    def _draw_crossings(self, frame, crossings):
        """Draw recent crossing events."""
        for crossing in crossings[-5:]:  # Show last 5 crossings
            # This would show crossing points if we had them
            pass
    
    def _draw_help(self, frame):
        """Draw help overlay."""
        height, width = frame.shape[:2]
        
        help_text = [
            "CONTROLS:",
            "'q' - Quit",
            "'r' - Reset counts",
            "'s' - Screenshot",
            "'h' - Toggle help",
            "'SPACE' - Pause"
        ]
        
        # Draw help background
        help_width = 200
        help_height = len(help_text) * 25 + 20
        start_x = width - help_width - 10
        
        cv2.rectangle(frame, (start_x, 10), (width - 10, help_height), 
                     self.colors['background'], -1)
        cv2.rectangle(frame, (start_x, 10), (width - 10, help_height), 
                     self.colors['text'], 2)
        
        # Draw help text
        for i, text in enumerate(help_text):
            y_pos = 35 + i * 25
            cv2.putText(frame, text, (start_x + 10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
    
    def toggle_help_display(self):
        """Toggle help display on/off."""
        self.show_help = not self.show_help


def create_overlay_manager():
    """Factory function to create overlay manager."""
    return SimpleOverlayManager()