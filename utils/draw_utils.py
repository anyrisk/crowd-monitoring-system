"""
Drawing utilities for the Smart Temple People Counter.
Helper functions for drawing bounding boxes, lines, text, and other visual elements.
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from utils.config import get_config


def draw_bounding_box(frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                     color: Tuple[int, int, int] = (255, 0, 0), 
                     thickness: int = 2, label: str = None, 
                     confidence: float = None) -> np.ndarray:
    """
    Draw a bounding box on the frame.
    
    Args:
        frame: Input frame
        bbox: Bounding box coordinates (x1, y1, x2, y2)
        color: Box color in BGR format
        thickness: Line thickness
        label: Optional label text
        confidence: Optional confidence score
        
    Returns:
        Frame with bounding box drawn
    """
    x1, y1, x2, y2 = bbox
    
    # Draw rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label if provided
    if label or confidence is not None:
        label_text = ""
        if label:
            label_text += label
        if confidence is not None:
            if label_text:
                label_text += f" ({confidence:.2f})"
            else:
                label_text = f"{confidence:.2f}"
        
        # Calculate label background size
        (label_width, label_height), baseline = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        
        # Draw label background
        cv2.rectangle(frame, (x1, y1 - label_height - 10), 
                     (x1 + label_width, y1), color, -1)
        
        # Draw label text
        cv2.putText(frame, label_text, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame


def draw_tracking_id(frame: np.ndarray, centroid: Tuple[int, int], 
                    object_id: int, color: Tuple[int, int, int] = (0, 255, 255)) -> np.ndarray:
    """
    Draw tracking ID at object centroid.
    
    Args:
        frame: Input frame
        centroid: Object center coordinates (x, y)
        object_id: Tracking ID number
        color: Text color in BGR format
        
    Returns:
        Frame with tracking ID drawn
    """
    x, y = centroid
    
    # Draw circle at centroid
    cv2.circle(frame, (x, y), 5, color, -1)
    
    # Draw ID text
    id_text = str(object_id)
    cv2.putText(frame, id_text, (x - 10, y - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


def draw_trajectory(frame: np.ndarray, points: List[Tuple[int, int]], 
                   color: Tuple[int, int, int] = (0, 255, 0), 
                   thickness: int = 2) -> np.ndarray:
    """
    Draw object trajectory as connected line segments.
    
    Args:
        frame: Input frame
        points: List of trajectory points
        color: Line color in BGR format
        thickness: Line thickness
        
    Returns:
        Frame with trajectory drawn
    """
    if len(points) < 2:
        return frame
    
    # Draw lines connecting trajectory points
    for i in range(1, len(points)):
        cv2.line(frame, points[i-1], points[i], color, thickness)
    
    return frame


def draw_counting_line(frame: np.ndarray, line_start: Tuple[int, int], 
                      line_end: Tuple[int, int], color: Tuple[int, int, int] = (0, 255, 0), 
                      thickness: int = 3, label: str = "Counting Line") -> np.ndarray:
    """
    Draw the counting line on the frame.
    
    Args:
        frame: Input frame
        line_start: Start point of the line
        line_end: End point of the line
        color: Line color in BGR format
        thickness: Line thickness
        label: Optional label for the line
        
    Returns:
        Frame with counting line drawn
    """
    # Draw the main line
    cv2.line(frame, line_start, line_end, color, thickness)
    
    # Draw arrow heads to show direction
    # Calculate line direction vector
    dx = line_end[0] - line_start[0]
    dy = line_end[1] - line_start[1]
    length = np.sqrt(dx*dx + dy*dy)
    
    if length > 0:
        # Normalize direction vector
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Calculate arrow points
        arrow_length = 20
        arrow_angle = 0.5  # radians
        
        # Arrow at end point
        arrow_x1 = int(line_end[0] - arrow_length * (dx_norm * np.cos(arrow_angle) - dy_norm * np.sin(arrow_angle)))
        arrow_y1 = int(line_end[1] - arrow_length * (dy_norm * np.cos(arrow_angle) + dx_norm * np.sin(arrow_angle)))
        arrow_x2 = int(line_end[0] - arrow_length * (dx_norm * np.cos(arrow_angle) + dy_norm * np.sin(arrow_angle)))
        arrow_y2 = int(line_end[1] - arrow_length * (dy_norm * np.cos(arrow_angle) - dx_norm * np.sin(arrow_angle)))
        
        cv2.line(frame, line_end, (arrow_x1, arrow_y1), color, thickness//2)
        cv2.line(frame, line_end, (arrow_x2, arrow_y2), color, thickness//2)
    
    # Draw label if provided
    if label:
        # Calculate label position (middle of line, offset upward)
        label_x = (line_start[0] + line_end[0]) // 2
        label_y = (line_start[1] + line_end[1]) // 2 - 20
        
        # Get text size for background
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
        )
        
        # Draw background rectangle
        cv2.rectangle(frame, (label_x - label_width//2 - 5, label_y - label_height - 5),
                     (label_x + label_width//2 + 5, label_y + 5), (0, 0, 0), -1)
        
        # Draw label text
        cv2.putText(frame, label, (label_x - label_width//2, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


def draw_count_display(frame: np.ndarray, counts: Dict[str, int], 
                      position: str = "top_left") -> np.ndarray:
    """
    Draw count statistics on the frame.
    
    Args:
        frame: Input frame
        counts: Dictionary with count statistics
        position: Position to draw ("top_left", "top_right", "bottom_left", "bottom_right")
        
    Returns:
        Frame with count display drawn
    """
    height, width = frame.shape[:2]
    
    # Prepare count text
    count_inside = counts.get('count_inside', 0)
    total_entered = counts.get('total_entered', 0)
    total_exited = counts.get('total_exited', 0)
    
    lines = [
        f"Inside: {count_inside}",
        f"Entered: {total_entered}",
        f"Exited: {total_exited}"
    ]
    
    # Calculate position
    line_height = 35
    margin = 20
    
    if position == "top_left":
        start_x, start_y = margin, margin + line_height
    elif position == "top_right":
        start_x, start_y = width - 200, margin + line_height
    elif position == "bottom_left":
        start_x, start_y = margin, height - len(lines) * line_height - margin
    else:  # bottom_right
        start_x, start_y = width - 200, height - len(lines) * line_height - margin
    
    # Draw background rectangle
    bg_width = 180
    bg_height = len(lines) * line_height + 20
    cv2.rectangle(frame, (start_x - 10, start_y - line_height - 10),
                 (start_x + bg_width, start_y + bg_height - line_height), 
                 (0, 0, 0), -1)
    
    # Draw border
    cv2.rectangle(frame, (start_x - 10, start_y - line_height - 10),
                 (start_x + bg_width, start_y + bg_height - line_height), 
                 (255, 255, 255), 2)
    
    # Draw count text
    for i, line in enumerate(lines):
        y_pos = start_y + i * line_height
        
        # Choose color based on count type
        if "Inside" in line:
            color = (0, 255, 255)  # Yellow
        elif "Entered" in line:
            color = (0, 255, 0)    # Green
        else:  # Exited
            color = (0, 0, 255)    # Red
        
        cv2.putText(frame, line, (start_x, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


def draw_alert_message(frame: np.ndarray, message: str, 
                      alert_type: str = "warning") -> np.ndarray:
    """
    Draw alert message prominently on the frame.
    
    Args:
        frame: Input frame
        message: Alert message text
        alert_type: Type of alert ("warning", "critical", "info")
        
    Returns:
        Frame with alert message drawn
    """
    height, width = frame.shape[:2]
    
    # Choose colors based on alert type
    if alert_type == "critical":
        bg_color = (0, 0, 255)      # Red background
        text_color = (255, 255, 255)  # White text
    elif alert_type == "warning":
        bg_color = (0, 165, 255)    # Orange background
        text_color = (0, 0, 0)      # Black text
    else:  # info
        bg_color = (255, 255, 0)    # Cyan background
        text_color = (0, 0, 0)      # Black text
    
    # Calculate text size and position
    font_scale = 1.0
    thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(
        message, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )
    
    # Center the message
    x = (width - text_width) // 2
    y = 60
    
    # Draw background rectangle
    padding = 20
    cv2.rectangle(frame, (x - padding, y - text_height - padding),
                 (x + text_width + padding, y + padding), bg_color, -1)
    
    # Draw border
    cv2.rectangle(frame, (x - padding, y - text_height - padding),
                 (x + text_width + padding, y + padding), (255, 255, 255), 3)
    
    # Draw alert text
    cv2.putText(frame, message, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
               font_scale, text_color, thickness)
    
    return frame


def draw_fps_counter(frame: np.ndarray, fps: float, 
                    position: Tuple[int, int] = None) -> np.ndarray:
    """
    Draw FPS counter on the frame.
    
    Args:
        frame: Input frame
        fps: Current FPS value
        position: Position to draw FPS counter
        
    Returns:
        Frame with FPS counter drawn
    """
    if position is None:
        height, width = frame.shape[:2]
        position = (width - 120, 30)
    
    fps_text = f"FPS: {fps:.1f}"
    
    # Draw background
    (text_width, text_height), baseline = cv2.getTextSize(
        fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    )
    
    x, y = position
    cv2.rectangle(frame, (x - 5, y - text_height - 5),
                 (x + text_width + 5, y + 5), (0, 0, 0), -1)
    
    # Draw FPS text
    color = (0, 255, 0) if fps >= 15 else (0, 165, 255) if fps >= 10 else (0, 0, 255)
    cv2.putText(frame, fps_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return frame


def draw_detection_confidence(frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                            confidence: float) -> np.ndarray:
    """
    Draw confidence score near bounding box.
    
    Args:
        frame: Input frame
        bbox: Bounding box coordinates
        confidence: Confidence score (0-1)
        
    Returns:
        Frame with confidence score drawn
    """
    x1, y1, x2, y2 = bbox
    
    # Choose color based on confidence
    if confidence >= 0.8:
        color = (0, 255, 0)    # Green for high confidence
    elif confidence >= 0.6:
        color = (0, 255, 255)  # Yellow for medium confidence
    else:
        color = (0, 165, 255)  # Orange for low confidence
    
    conf_text = f"{confidence:.2f}"
    cv2.putText(frame, conf_text, (x2 - 60, y1 + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame


def create_legend(frame_width: int, frame_height: int) -> np.ndarray:
    """
    Create a legend explaining the visual elements.
    
    Args:
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        Legend image as numpy array
    """
    config = get_config()
    
    # Create legend background
    legend_height = 200
    legend = np.zeros((legend_height, frame_width, 3), dtype=np.uint8)
    
    # Legend items
    items = [
        ("Person Detection", config.COLORS["person_box"]),
        ("Tracking ID", config.COLORS["tracking_id"]),
        ("Counting Line", config.COLORS["counting_line"]),
        ("Entry Point", config.COLORS["entry_point"]),
        ("Exit Point", config.COLORS["exit_point"])
    ]
    
    # Draw legend items
    x_start = 20
    y_start = 30
    item_height = 30
    
    for i, (label, color) in enumerate(items):
        y = y_start + i * item_height
        
        # Draw color indicator
        cv2.rectangle(legend, (x_start, y - 10), (x_start + 20, y + 10), color, -1)
        
        # Draw label
        cv2.putText(legend, label, (x_start + 30, y + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return legend