"""
Simple object tracker for the Crowd Monitoring System.
Basic centroid-based tracking for demonstration purposes.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from scipy.spatial import distance as dist


class SimpleTracker:
    """Simple centroid-based object tracker."""
    
    def __init__(self, max_disappeared=15, max_distance=80):
        """
        Initialize the tracker.
        
        Args:
            max_disappeared: Max frames before object is considered gone
            max_distance: Max distance for object association
        """
        self.next_object_id = 0
        self.objects = {}  # {object_id: centroid}
        self.disappeared = {}  # {object_id: disappeared_count}
        self.object_history = {}  # {object_id: [list of recent positions]}
        
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.history_length = 10  # Keep last 10 positions for smoothing
    
    def register(self, centroid):
        """Register a new object."""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.object_history[self.next_object_id] = [centroid]
        self.next_object_id += 1
    
    def deregister(self, object_id):
        """Deregister an object."""
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.object_history:
            del self.object_history[object_id]
    
    def update(self, detections):
        """
        Update tracker with new detections.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Dictionary of tracked objects {id: {centroid: (x,y), bbox: (x1,y1,x2,y2)}}
        """
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            return {}
        
        # Extract centroids from detections
        input_centroids = []
        for detection in detections:
            centroid = detection['center']
            input_centroids.append(centroid)
        
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.register(centroid)
        
        else:
            # Match existing objects to new detections
            object_centroids = list(self.objects.values())
            object_ids = list(self.objects.keys())
            
            # Compute distance matrix
            D = dist.cdist(np.array(object_centroids), input_centroids)
            
            # Find minimum values and sort by distance
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            # Keep track of used row and column indices
            used_row_indices = set()
            used_col_indices = set()
            
            # Update existing objects
            for (row, col) in zip(rows, cols):
                if row in used_row_indices or col in used_col_indices:
                    continue
                
                if D[row, col] > self.max_distance:
                    continue
                
                # Update object position with smoothing
                object_id = object_ids[row]
                new_centroid = input_centroids[col]
                
                # Add to history
                if object_id in self.object_history:
                    self.object_history[object_id].append(new_centroid)
                    if len(self.object_history[object_id]) > self.history_length:
                        self.object_history[object_id] = self.object_history[object_id][-self.history_length:]
                
                # Use smoothed position
                self.objects[object_id] = new_centroid
                self.disappeared[object_id] = 0
                
                used_row_indices.add(row)
                used_col_indices.add(col)
            
            # Handle unmatched detections and objects
            unused_row_indices = set(range(0, D.shape[0])).difference(used_row_indices)
            unused_col_indices = set(range(0, D.shape[1])).difference(used_col_indices)
            
            # If more objects than detections, mark objects as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_row_indices:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            
            # If more detections than objects, register new objects
            else:
                for col in unused_col_indices:
                    self.register(input_centroids[col])
        
        # Create return dictionary with additional info
        tracked_objects = {}
        for i, (object_id, centroid) in enumerate(self.objects.items()):
            # Find corresponding detection
            detection = None
            for det in detections:
                if det['center'] == centroid:
                    detection = det
                    break
            
            tracked_objects[object_id] = {
                'centroid': centroid,
                'bbox': detection['bbox'] if detection else None,
                'confidence': detection['confidence'] if detection else 0.0
            }
        
        return tracked_objects


def create_tracker():
    """Factory function to create tracker."""
    return SimpleTracker()