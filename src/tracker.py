"""
Object tracking module for the Smart Crowd Monitoring System.
Assigns and maintains unique IDs for detected people across video frames using centroid tracking.
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Set, Optional
from collections import OrderedDict
import logging
from datetime import datetime

from utils.config import get_config
from utils.logger import default_logger


class CentroidTracker:
    """
    Simple centroid-based object tracker for person tracking.
    Based on the centroid tracking algorithm with improvements for people counting.
    """
    
    def __init__(self, max_disappeared: int = None, max_distance: int = None, 
                 logger: logging.Logger = None):
        """
        Initialize the centroid tracker.
        
        Args:
            max_disappeared (int): Maximum number of frames an object can disappear before removal
            max_distance (int): Maximum distance for object association
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        
        # Tracking parameters
        self.max_disappeared = max_disappeared or self.config.MAX_DISAPPEARED
        self.max_distance = max_distance or self.config.MAX_DISTANCE
        
        # Tracking state
        self.next_object_id = 0
        self.objects = OrderedDict()  # {object_id: centroid}
        self.disappeared = OrderedDict()  # {object_id: frames_disappeared}
        self.object_history = OrderedDict()  # {object_id: [list of centroids]}
        
        # Additional tracking data
        self.object_bboxes = OrderedDict()  # {object_id: bbox}
        self.object_confidences = OrderedDict()  # {object_id: confidence}
        self.object_first_seen = OrderedDict()  # {object_id: timestamp}
        self.object_last_seen = OrderedDict()  # {object_id: timestamp}
    
    def register(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int] = None, 
                confidence: float = None) -> int:
        """
        Register a new object with a unique ID.
        
        Args:
            centroid (Tuple[int, int]): (x, y) coordinates of object center
            bbox (Tuple[int, int, int, int]): Bounding box (x1, y1, x2, y2)
            confidence (float): Detection confidence score
            
        Returns:
            int: Assigned object ID
        """
        object_id = self.next_object_id
        
        # Store object data
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.object_history[object_id] = [centroid]
        
        if bbox is not None:
            self.object_bboxes[object_id] = bbox
        
        if confidence is not None:
            self.object_confidences[object_id] = confidence
        
        # Timestamps
        current_time = datetime.now()
        self.object_first_seen[object_id] = current_time
        self.object_last_seen[object_id] = current_time
        
        # Increment ID for next object
        self.next_object_id += 1
        
        self.logger.debug(f"Registered new object {object_id} at {centroid}")
        return object_id
    
    def deregister(self, object_id: int):
        """
        Remove an object from tracking.
        
        Args:
            object_id (int): ID of object to remove
        """
        if object_id in self.objects:
            self.logger.debug(f"Deregistered object {object_id}")
            
            # Remove from all tracking dictionaries
            del self.objects[object_id]
            del self.disappeared[object_id]
            del self.object_history[object_id]
            
            # Remove optional data if present
            if object_id in self.object_bboxes:
                del self.object_bboxes[object_id]
            if object_id in self.object_confidences:
                del self.object_confidences[object_id]
            if object_id in self.object_first_seen:
                del self.object_first_seen[object_id]
            if object_id in self.object_last_seen:
                del self.object_last_seen[object_id]
    
    def update(self, detections: List[Dict]) -> Dict[int, Dict]:
        """
        Update tracker with new detections.
        
        Args:
            detections (List[Dict]): List of detection dictionaries from detector
            
        Returns:
            Dict mapping object IDs to their tracking information
        """
        # If no detections, increment disappeared counter for all objects
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                # Remove objects that have disappeared for too long
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            return self._get_tracking_results()
        
        # Extract centroids from detections
        input_centroids = []
        input_data = []
        
        for detection in detections:
            centroid = detection['center']
            input_centroids.append(centroid)
            input_data.append({
                'centroid': centroid,
                'bbox': detection.get('bbox'),
                'confidence': detection.get('confidence')
            })
        
        # If no existing objects, register all detections as new objects
        if len(self.objects) == 0:
            for data in input_data:
                self.register(data['centroid'], data['bbox'], data['confidence'])
        
        else:
            # Compute distance matrix between existing objects and new detections
            object_centroids = list(self.objects.values())
            object_ids = list(self.objects.keys())
            
            D = self._compute_distance_matrix(object_centroids, input_centroids)
            
            # Find the minimum values and sort by distance
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            # Keep track of used row and column indices
            used_row_idxs = set()
            used_col_idxs = set()
            
            # Loop over the (row, column) index tuples
            for (row, col) in zip(rows, cols):
                # If we have already examined this row or column, ignore it
                if row in used_row_idxs or col in used_col_idxs:
                    continue
                
                # If the distance is too large, skip this pairing
                if D[row, col] > self.max_distance:
                    continue
                
                # Update existing object
                object_id = object_ids[row]
                new_centroid = input_centroids[col]
                
                self.objects[object_id] = new_centroid
                self.disappeared[object_id] = 0
                
                # Update additional data
                detection_data = input_data[col]
                if detection_data['bbox'] is not None:
                    self.object_bboxes[object_id] = detection_data['bbox']
                if detection_data['confidence'] is not None:
                    self.object_confidences[object_id] = detection_data['confidence']
                
                # Update history and timestamps
                self.object_history[object_id].append(new_centroid)
                self.object_last_seen[object_id] = datetime.now()
                
                # Limit history length to prevent memory issues
                if len(self.object_history[object_id]) > 100:
                    self.object_history[object_id] = self.object_history[object_id][-50:]
                
                # Mark this row and column as used
                used_row_idxs.add(row)
                used_col_idxs.add(col)
            
            # Handle unmatched detections and objects
            unused_row_idxs = set(range(0, D.shape[0])) - used_row_idxs
            unused_col_idxs = set(range(0, D.shape[1])) - used_col_idxs
            
            # If there are more objects than detections, mark objects as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_row_idxs:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    
                    # Remove if disappeared for too long
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            
            # If there are more detections than objects, register new objects
            else:
                for col in unused_col_idxs:
                    detection_data = input_data[col]
                    self.register(detection_data['centroid'], 
                                detection_data['bbox'], 
                                detection_data['confidence'])
        
        return self._get_tracking_results()
    
    def _compute_distance_matrix(self, object_centroids: List[Tuple[int, int]], 
                               input_centroids: List[Tuple[int, int]]) -> np.ndarray:
        """
        Compute Euclidean distance matrix between object centroids and input centroids.
        
        Args:
            object_centroids (List[Tuple[int, int]]): Existing object centroids
            input_centroids (List[Tuple[int, int]]): New detection centroids
            
        Returns:
            np.ndarray: Distance matrix
        """
        # Convert to numpy arrays
        existing = np.array(object_centroids)
        detections = np.array(input_centroids)
        
        # Compute distance matrix using broadcasting
        D = np.linalg.norm(existing[:, np.newaxis] - detections, axis=2)
        
        return D
    
    def _get_tracking_results(self) -> Dict[int, Dict]:
        """
        Get current tracking results.
        
        Returns:
            Dict mapping object IDs to their tracking information
        """
        results = {}
        
        for object_id in self.objects.keys():
            results[object_id] = {
                'centroid': self.objects[object_id],
                'bbox': self.object_bboxes.get(object_id),
                'confidence': self.object_confidences.get(object_id),
                'first_seen': self.object_first_seen.get(object_id),
                'last_seen': self.object_last_seen.get(object_id),
                'history': self.object_history.get(object_id, []),
                'disappeared_frames': self.disappeared[object_id]
            }
        
        return results
    
    def get_object_trajectory(self, object_id: int) -> List[Tuple[int, int]]:
        """
        Get the trajectory (history of centroids) for a specific object.
        
        Args:
            object_id (int): Object ID
            
        Returns:
            List of (x, y) coordinates representing the object's path
        """
        return self.object_history.get(object_id, [])
    
    def get_object_direction(self, object_id: int, frames: int = 5) -> Optional[Tuple[float, float]]:
        """
        Estimate movement direction for an object based on recent trajectory.
        
        Args:
            object_id (int): Object ID
            frames (int): Number of recent frames to consider
            
        Returns:
            Tuple of (dx, dy) direction vector, or None if insufficient data
        """
        if object_id not in self.object_history:
            return None
        
        history = self.object_history[object_id]
        if len(history) < 2:
            return None
        
        # Use recent frames for direction calculation
        recent_points = history[-frames:] if len(history) >= frames else history
        
        if len(recent_points) < 2:
            return None
        
        # Calculate direction vector from first to last point
        start_point = recent_points[0]
        end_point = recent_points[-1]
        
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        
        # Normalize if movement is significant
        magnitude = np.sqrt(dx*dx + dy*dy)
        if magnitude > 5:  # Minimum movement threshold
            return (dx / magnitude, dy / magnitude)
        
        return None
    
    def get_active_objects(self) -> Dict[int, Dict]:
        """
        Get all currently active (not disappeared) objects.
        
        Returns:
            Dict of active object tracking information
        """
        active_objects = {}
        
        for object_id, disappeared_count in self.disappeared.items():
            if disappeared_count == 0:  # Object is currently visible
                active_objects[object_id] = self._get_tracking_results()[object_id]
        
        return active_objects
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get tracker statistics.
        
        Returns:
            Dict with tracker statistics
        """
        active_count = sum(1 for count in self.disappeared.values() if count == 0)
        
        return {
            'total_objects': len(self.objects),
            'active_objects': active_count,
            'disappeared_objects': len(self.objects) - active_count,
            'next_id': self.next_object_id
        }
    
    def reset(self):
        """Reset the tracker, removing all objects."""
        self.objects.clear()
        self.disappeared.clear()
        self.object_history.clear()
        self.object_bboxes.clear()
        self.object_confidences.clear()
        self.object_first_seen.clear()
        self.object_last_seen.clear()
        self.next_object_id = 0
        
        self.logger.info("Tracker reset - all objects cleared")
    
    def update_parameters(self, max_disappeared: int = None, max_distance: int = None):
        """
        Update tracker parameters.
        
        Args:
            max_disappeared (int): Maximum frames before object removal
            max_distance (int): Maximum distance for object association
        """
        if max_disappeared is not None:
            self.max_disappeared = max_disappeared
            self.logger.info(f"Updated max_disappeared to {max_disappeared}")
        
        if max_distance is not None:
            self.max_distance = max_distance
            self.logger.info(f"Updated max_distance to {max_distance}")


def create_tracker(max_disappeared: int = None, max_distance: int = None) -> CentroidTracker:
    """
    Factory function to create a CentroidTracker instance.
    
    Args:
        max_disappeared (int): Maximum frames before object removal
        max_distance (int): Maximum distance for object association
        
    Returns:
        CentroidTracker instance
    """
    return CentroidTracker(max_disappeared=max_disappeared, max_distance=max_distance)