"""
Improved counter for accurate people counting.
Optimized for right-to-left entry and left-to-right exit detection.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

from utils.config import get_config
from utils.logger import default_logger
from src.database import get_database_manager


class CrossingDirection(Enum):
    """Enumeration for crossing directions."""
    ENTRY = "entry"
    EXIT = "exit"
    NONE = "none"


class ImprovedPeopleCounter:
    """
    Improved people counter with better accuracy for horizontal movement detection.
    """
    
    def __init__(self):
        """Initialize the improved counter."""
        self.config = get_config()
        self.logger = default_logger
        self.db_manager = get_database_manager()
        
        # Counting state
        self.count_inside = 0
        self.total_entered = 0
        self.total_exited = 0
        
        # Tracking state for crossing detection
        self.object_trajectories = {}  # {object_id: [list of (x, y, timestamp)]}
        self.crossed_objects = set()  # Objects that have already been counted
        self.trajectory_length = 8  # Number of points to track
        
        # Virtual counting zone (invisible)
        self.counting_zone_x = 0.5  # Middle of frame (50%)
        self.zone_width = 0.3  # 30% of frame width (wider detection zone)
        
        # Movement thresholds (optimized for laptop camera)
        self.min_movement_distance = 80   # Minimum pixels moved to count (reduced for closer laptop camera)
        self.min_trajectory_points = 3    # Minimum points needed (faster detection)
        
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
    
    def update(self, tracked_objects: Dict[int, Dict], frame_width: int, frame_height: int) -> List:
        """
        Update counter with tracked objects and detect crossings.
        
        Args:
            tracked_objects: Dictionary of tracked objects from tracker
            frame_width: Width of video frame
            frame_height: Height of video frame
            
        Returns:
            List of crossing events detected
        """
        crossings = []
        current_time = datetime.now()
        
        # Calculate counting zone boundaries
        zone_left = int(frame_width * (self.counting_zone_x - self.zone_width/2))
        zone_right = int(frame_width * (self.counting_zone_x + self.zone_width/2))
        
        # Process each tracked object
        for object_id, obj_data in tracked_objects.items():
            centroid = obj_data['centroid']
            
            # Initialize trajectory if new object
            if object_id not in self.object_trajectories:
                self.object_trajectories[object_id] = []
            
            # Add current position to trajectory
            self.object_trajectories[object_id].append((centroid[0], centroid[1], current_time))
            
            # Keep only recent trajectory points
            if len(self.object_trajectories[object_id]) > self.trajectory_length:
                self.object_trajectories[object_id] = self.object_trajectories[object_id][-self.trajectory_length:]
            
            # Check for crossing if we have enough trajectory points
            traj_len = len(self.object_trajectories[object_id])
            if traj_len >= self.min_trajectory_points and object_id not in self.crossed_objects:
                
                # Debug: Print trajectory info every few frames
                if traj_len % 5 == 0:
                    start_pos = self.object_trajectories[object_id][0]
                    end_pos = self.object_trajectories[object_id][-1]
                    movement = abs(end_pos[0] - start_pos[0])
                    print(f"Object {object_id}: trajectory={traj_len}, movement={movement:.1f}px, start_x={start_pos[0]}, end_x={end_pos[0]}")
                
                crossing = self._detect_crossing(object_id, zone_left, zone_right, frame_width)
                
                if crossing:
                    crossings.append(crossing)
                    self._process_crossing(crossing)
                    self.crossed_objects.add(object_id)
        
        # Clean up old trajectories for objects no longer tracked
        current_object_ids = set(tracked_objects.keys())
        old_object_ids = set(self.object_trajectories.keys()) - current_object_ids
        
        for old_id in old_object_ids:
            del self.object_trajectories[old_id]
            self.crossed_objects.discard(old_id)
        
        return crossings
    
    def _detect_crossing(self, object_id: int, zone_left: int, zone_right: int, frame_width: int) -> Optional[Dict]:
        """
        Detect if an object has crossed the counting zone.
        
        Args:
            object_id: ID of the tracked object
            zone_left: Left boundary of counting zone
            zone_right: Right boundary of counting zone
            frame_width: Width of the frame
            
        Returns:
            Crossing event dictionary if crossing detected, None otherwise
        """
        trajectory = self.object_trajectories[object_id]
        
        if len(trajectory) < self.min_trajectory_points:
            return None
        
        # Get start and end positions
        start_pos = trajectory[0]
        end_pos = trajectory[-1]
        
        start_x, start_y = start_pos[0], start_pos[1]
        end_x, end_y = end_pos[0], end_pos[1]
        
        # Calculate total movement distance
        movement_distance = abs(end_x - start_x)
        
        # Check if movement is significant enough
        if movement_distance < self.min_movement_distance:
            return None
        
        # Simplified zone crossing - just check if object moved across center area
        center_x = frame_width * 0.5
        
        # Check if trajectory crosses the center area
        crossed_center = False
        for i in range(len(trajectory) - 1):
            curr_x = trajectory[i][0]
            next_x = trajectory[i + 1][0]
            
            # Check if movement crosses the center line
            if ((curr_x < center_x and next_x > center_x) or 
                (curr_x > center_x and next_x < center_x)):
                crossed_center = True
                break
        
        if not crossed_center:
            print(f"Object {object_id}: No center crossing detected")
            return None
        
        # Determine direction based on overall movement (optimized for laptop camera)
        movement_threshold = frame_width * 0.15  # 15% of frame width
        
        if start_x > end_x and movement_distance > movement_threshold:
            # Right to Left = ENTRY (moved leftward significantly)
            direction = CrossingDirection.ENTRY
            print(f"✅ ENTRY detected: Object {object_id} moved R->L ({start_x:.0f} to {end_x:.0f}, distance: {movement_distance:.0f}px)")
        elif end_x > start_x and movement_distance > movement_threshold:
            # Left to Right = EXIT (moved rightward significantly)
            direction = CrossingDirection.EXIT
            print(f"🚪 EXIT detected: Object {object_id} moved L->R ({start_x:.0f} to {end_x:.0f}, distance: {movement_distance:.0f}px)")
        else:
            return None
        
        return {
            'object_id': object_id,
            'direction': direction,
            'timestamp': datetime.now(),
            'start_pos': (start_x, start_y),
            'end_pos': (end_x, end_y),
            'movement_distance': movement_distance
        }
    
    def _process_crossing(self, crossing: Dict):
        """
        Process a detected crossing event and update counts.
        
        Args:
            crossing: Crossing event dictionary
        """
        try:
            direction = crossing['direction']
            object_id = crossing['object_id']
            
            if direction == CrossingDirection.ENTRY:
                self.count_inside += 1
                self.total_entered += 1
                event_type = "entry"
                
                print(f"✅ ENTRY detected: Person {object_id} | Inside: {self.count_inside}")
                
            elif direction == CrossingDirection.EXIT:
                self.count_inside = max(0, self.count_inside - 1)  # Prevent negative counts
                self.total_exited += 1
                event_type = "exit"
                
                print(f"🚪 EXIT detected: Person {object_id} | Inside: {self.count_inside}")
            
            else:
                return
            
            # Log to database
            self.db_manager.log_event(
                event_type=event_type,
                person_id=object_id,
                count_inside=self.count_inside,
                total_entered=self.total_entered,
                total_exited=self.total_exited
            )
            
            # Log to application logger
            self.logger.info(f"Crossing detected: {event_type} by person {object_id}, "
                           f"count inside: {self.count_inside}")
        
        except Exception as e:
            self.logger.error(f"Error processing crossing event: {e}")
    
    def get_counts(self) -> Dict[str, int]:
        """Get current counting statistics."""
        return {
            'count_inside': self.count_inside,
            'total_entered': self.total_entered,
            'total_exited': self.total_exited
        }
    
    def reset_counts(self, notes: str = "Manual reset") -> bool:
        """Reset all counts to zero."""
        try:
            # Reset internal counters
            self.count_inside = 0
            self.total_entered = 0
            self.total_exited = 0
            
            # Clear tracking state
            self.object_trajectories.clear()
            self.crossed_objects.clear()
            
            # Log reset event to database
            success = self.db_manager.reset_counts(notes)
            
            if success:
                self.logger.info("Counts reset successfully")
                print("🔄 All counts reset to zero")
            else:
                self.logger.error("Failed to reset counts in database")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error resetting counts: {e}")
            return False


def create_counter():
    """Factory function to create an ImprovedPeopleCounter instance."""
    return ImprovedPeopleCounter()