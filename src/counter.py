"""
Line-crossing counter module for the Smart Crowd Monitoring System.
Implements virtual line crossing detection to count entries and exits.
"""

import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from datetime import datetime

from utils.config import get_config
from utils.logger import default_logger, log_detection_event
from src.database import get_database_manager


class CrossingDirection(Enum):
    """Enumeration for crossing directions."""
    ENTRY = "entry"
    EXIT = "exit"
    NONE = "none"


class LineCrossing:
    """Represents a line crossing event."""
    
    def __init__(self, object_id: int, direction: CrossingDirection, 
                 timestamp: datetime, crossing_point: Tuple[int, int]):
        self.object_id = object_id
        self.direction = direction
        self.timestamp = timestamp
        self.crossing_point = crossing_point


class PeopleCounter:
    """
    Implements line-crossing based people counting with entry/exit detection.
    """
    
    def __init__(self, counting_line: Dict = None, logger: logging.Logger = None):
        """
        Initialize the people counter.
        
        Args:
            counting_line (Dict): Line configuration with start/end points
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        self.db_manager = get_database_manager()
        
        # Counting line configuration
        self.counting_line = counting_line or self.config.COUNTING_LINE
        
        # Counting state
        self.count_inside = 0
        self.total_entered = 0
        self.total_exited = 0
        
        # Tracking state for line crossing detection
        self.object_positions = {}  # {object_id: [list of positions]}
        self.crossed_objects = set()  # Objects that have already crossed (to prevent double counting)
        self.crossing_buffer = 5  # Number of frames to track for crossing detection
        
        # Line crossing events history
        self.recent_crossings = []
        self.max_history = 100
        
        # Load current counts from database
        self._load_current_counts()
    
    def _load_current_counts(self):
        """Load current counts from database."""
        try:
            current_stats = self.db_manager.get_current_count()
            self.count_inside = current_stats['count_inside']
            self.total_entered = current_stats['total_entered']
            self.total_exited = current_stats['total_exited']
            
            self.logger.info(f"Loaded counts: Inside={self.count_inside}, "
                           f"Entered={self.total_entered}, Exited={self.total_exited}")
        except Exception as e:
            self.logger.error(f"Error loading current counts: {e}")
    
    def update(self, tracked_objects: Dict[int, Dict], frame_width: int, frame_height: int) -> List[LineCrossing]:
        """
        Update counter with tracked objects and detect line crossings.
        
        Args:
            tracked_objects (Dict): Dictionary of tracked objects from tracker
            frame_width (int): Width of video frame
            frame_height (int): Height of video frame
            
        Returns:
            List of LineCrossing events detected in this update
        """
        crossings = []
        
        # Get line coordinates in pixel values
        line_start, line_end = self.config.get_counting_line_coords(frame_width, frame_height)
        
        # Process each tracked object
        for object_id, obj_data in tracked_objects.items():
            centroid = obj_data['centroid']
            
            # Update position history for this object
            if object_id not in self.object_positions:
                self.object_positions[object_id] = []
            
            self.object_positions[object_id].append(centroid)
            
            # Keep only recent positions
            if len(self.object_positions[object_id]) > self.crossing_buffer:
                self.object_positions[object_id] = self.object_positions[object_id][-self.crossing_buffer:]
            
            # Check for line crossing
            if len(self.object_positions[object_id]) >= 2:
                crossing = self._detect_line_crossing(
                    object_id, 
                    self.object_positions[object_id],
                    line_start, 
                    line_end
                )
                
                if crossing and object_id not in self.crossed_objects:
                    crossings.append(crossing)
                    self._process_crossing(crossing)
                    
                    # Mark object as crossed to prevent double counting
                    self.crossed_objects.add(object_id)
        
        # Clean up old object positions for objects that are no longer tracked
        current_object_ids = set(tracked_objects.keys())
        old_object_ids = set(self.object_positions.keys()) - current_object_ids
        
        for old_id in old_object_ids:
            del self.object_positions[old_id]
            self.crossed_objects.discard(old_id)
        
        return crossings
    
    def _detect_line_crossing(self, object_id: int, positions: List[Tuple[int, int]], 
                            line_start: Tuple[int, int], line_end: Tuple[int, int]) -> Optional[LineCrossing]:
        """
        Detect if an object has crossed the counting line.
        
        Args:
            object_id (int): ID of the tracked object
            positions (List[Tuple[int, int]]): Recent positions of the object
            line_start (Tuple[int, int]): Start point of counting line
            line_end (Tuple[int, int]): End point of counting line
            
        Returns:
            LineCrossing event if crossing detected, None otherwise
        """
        if len(positions) < 2:
            return None
        
        # Check the last two positions for line crossing
        prev_pos = positions[-2]
        curr_pos = positions[-1]
        
        # Check if the object trajectory intersects with the counting line
        intersection = self._line_intersection(prev_pos, curr_pos, line_start, line_end)
        
        if intersection:
            # Determine crossing direction based on object movement
            direction = self._determine_crossing_direction(prev_pos, curr_pos, line_start, line_end)
            
            if direction != CrossingDirection.NONE:
                return LineCrossing(
                    object_id=object_id,
                    direction=direction,
                    timestamp=datetime.now(),
                    crossing_point=intersection
                )
        
        return None
    
    def _line_intersection(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                          p3: Tuple[int, int], p4: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Check if two line segments intersect and return intersection point.
        
        Args:
            p1, p2: Points defining the first line segment (object trajectory)
            p3, p4: Points defining the second line segment (counting line)
            
        Returns:
            Intersection point if lines intersect, None otherwise
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        # Calculate the direction vectors
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        # Lines are parallel
        if abs(denom) < 1e-6:
            return None
        
        # Calculate intersection parameters
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        # Check if intersection point is within both line segments
        if 0 <= t <= 1 and 0 <= u <= 1:
            # Calculate intersection point
            ix = int(x1 + t * (x2 - x1))
            iy = int(y1 + t * (y2 - y1))
            return (ix, iy)
        
        return None
    
    def _determine_crossing_direction(self, prev_pos: Tuple[int, int], curr_pos: Tuple[int, int],
                                   line_start: Tuple[int, int], line_end: Tuple[int, int]) -> CrossingDirection:
        """
        Determine the direction of crossing based on object movement and line orientation.
        
        Args:
            prev_pos, curr_pos: Previous and current object positions
            line_start, line_end: Start and end points of counting line
            
        Returns:
            CrossingDirection indicating entry, exit, or none
        """
        # Calculate which side of the line each position is on
        prev_side = self._point_side_of_line(prev_pos, line_start, line_end)
        curr_side = self._point_side_of_line(curr_pos, line_start, line_end)
        
        # If positions are on different sides, a crossing occurred
        if prev_side != curr_side and prev_side != 0 and curr_side != 0:
            # Determine direction based on configuration and line orientation
            if self.config.ENTRY_DIRECTION == "right_to_left":
                # Entry is from positive to negative side (right to left)
                if prev_side > 0 and curr_side < 0:
                    return CrossingDirection.ENTRY
                elif prev_side < 0 and curr_side > 0:
                    return CrossingDirection.EXIT
            else:  # "left_to_right"
                # Entry is from negative to positive side (left to right)
                if prev_side < 0 and curr_side > 0:
                    return CrossingDirection.ENTRY
                elif prev_side > 0 and curr_side < 0:
                    return CrossingDirection.EXIT
        
        return CrossingDirection.NONE
    
    def _point_side_of_line(self, point: Tuple[int, int], line_start: Tuple[int, int], 
                          line_end: Tuple[int, int]) -> int:
        """
        Determine which side of a line a point is on.
        
        Args:
            point: Point to test
            line_start, line_end: Line definition points
            
        Returns:
            Positive if point is on right/above, negative if left/below, 0 if on line
        """
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Use cross product to determine side
        cross_product = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        
        if cross_product > 0:
            return 1
        elif cross_product < 0:
            return -1
        else:
            return 0
    
    def _process_crossing(self, crossing: LineCrossing):
        """
        Process a detected crossing event and update counts.
        
        Args:
            crossing: LineCrossing event to process
        """
        try:
            if crossing.direction == CrossingDirection.ENTRY:
                self.count_inside += 1
                self.total_entered += 1
                event_type = "entry"
                
            elif crossing.direction == CrossingDirection.EXIT:
                self.count_inside = max(0, self.count_inside - 1)  # Prevent negative counts
                self.total_exited += 1
                event_type = "exit"
            
            else:
                return
            
            # Log to database
            self.db_manager.log_event(
                event_type=event_type,
                person_id=crossing.object_id,
                count_inside=self.count_inside,
                total_entered=self.total_entered,
                total_exited=self.total_exited
            )
            
            # Log to application logger
            log_detection_event(
                self.logger, 
                event_type, 
                crossing.object_id, 
                self.count_inside
            )
            
            # Add to recent crossings history
            self.recent_crossings.append(crossing)
            if len(self.recent_crossings) > self.max_history:
                self.recent_crossings = self.recent_crossings[-self.max_history//2:]
        
        except Exception as e:
            self.logger.error(f"Error processing crossing event: {e}")
    
    def get_counts(self) -> Dict[str, int]:
        """
        Get current counting statistics.
        
        Returns:
            Dictionary with current counts
        """
        return {
            'count_inside': self.count_inside,
            'total_entered': self.total_entered,
            'total_exited': self.total_exited
        }
    
    def reset_counts(self, notes: str = "Manual reset") -> bool:
        """
        Reset all counts to zero.
        
        Args:
            notes: Reason for reset
            
        Returns:
            Success status
        """
        try:
            # Reset internal counters
            self.count_inside = 0
            self.total_entered = 0
            self.total_exited = 0
            
            # Clear tracking state
            self.object_positions.clear()
            self.crossed_objects.clear()
            self.recent_crossings.clear()
            
            # Log reset event to database
            success = self.db_manager.reset_counts(notes)
            
            if success:
                self.logger.info("Counts reset successfully")
            else:
                self.logger.error("Failed to reset counts in database")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error resetting counts: {e}")
            return False
    
    def update_counting_line(self, start_percent: Tuple[float, float], 
                           end_percent: Tuple[float, float]):
        """
        Update the counting line position.
        
        Args:
            start_percent: Start position as percentage of frame dimensions
            end_percent: End position as percentage of frame dimensions
        """
        self.config.update_counting_line(start_percent, end_percent)
        self.counting_line = self.config.COUNTING_LINE
        
        # Clear tracking state since line position changed
        self.object_positions.clear()
        self.crossed_objects.clear()
        
        self.logger.info(f"Updated counting line: {start_percent} to {end_percent}")
    
    def get_recent_crossings(self, limit: int = 10) -> List[LineCrossing]:
        """
        Get recent crossing events.
        
        Args:
            limit: Maximum number of recent crossings to return
            
        Returns:
            List of recent LineCrossing events
        """
        return self.recent_crossings[-limit:] if self.recent_crossings else []
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get detailed counting statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        return {
            'counts': self.get_counts(),
            'recent_crossings': len(self.recent_crossings),
            'tracked_objects': len(self.object_positions),
            'crossed_objects': len(self.crossed_objects),
            'counting_line': self.counting_line
        }


def create_counter(counting_line: Dict = None) -> PeopleCounter:
    """
    Factory function to create a PeopleCounter instance.
    
    Args:
        counting_line: Line configuration dictionary
        
    Returns:
        PeopleCounter instance
    """
    return PeopleCounter(counting_line=counting_line)