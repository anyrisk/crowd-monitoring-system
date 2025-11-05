"""
Human detection module using YOLOv5 for the Smart Crowd Monitoring System.
Handles loading the YOLO model and detecting people in video frames.
"""

import cv2
import torch
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import urllib.request
import os

from utils.config import get_config
from utils.logger import default_logger, log_system_event


class DummyYOLOModel:
    """Dummy YOLO model for testing when real models are not available."""
    
    def __init__(self):
        self.conf = 0.5
        self.iou = 0.4
        self.names = {0: 'person'}
        self.nc = 80
    
    def __call__(self, frame):
        """Dummy inference that returns no detections."""
        # Return empty results in the format expected by torch.hub YOLOv5
        import pandas as pd
        
        class DummyResults:
            def pandas(self):
                return DummyPandas()
        
        class DummyPandas:
            def __init__(self):
                self.xyxy = [pd.DataFrame(columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class', 'name'])]
        
        return DummyResults()


class PersonDetector:
    """
    YOLOv5-based person detection system.
    """
    
    def __init__(self, model_path: str = None, device: str = None, logger: logging.Logger = None):
        """
        Initialize the person detector.
        
        Args:
            model_path (str): Path to YOLO model file
            device (str): Device to run inference on ('cpu' or 'cuda')
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        
        # Set device
        self.device = device or self.config.DEVICE
        if self.device == 'cuda' and not torch.cuda.is_available():
            self.logger.warning("CUDA not available, falling back to CPU")
            self.device = 'cpu'
        
        # Model settings
        self.model_path = model_path or self.config.YOLO_MODEL_PATH
        self.confidence_threshold = self.config.CONFIDENCE_THRESHOLD
        self.nms_threshold = self.config.NMS_THRESHOLD
        
        # Class ID for person in COCO dataset (YOLOv5 default)
        self.person_class_id = 0
        
        # Initialize model
        self.model = None
        self.input_size = 640
        self.load_model()
    
    def load_model(self):
        """Load YOLOv5 model."""
        try:
            log_system_event(self.logger, "Loading YOLO model", self.model_path)
            
            # Check if model file exists, download if needed
            if not os.path.exists(self.model_path):
                self._download_default_model()
            
            # Load YOLOv5 model using torch.hub or ultralytics
            model_loaded = False
            
            # Try loading with ultralytics first (newer format)
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.model_type = 'ultralytics'
                model_loaded = True
                log_system_event(self.logger, "Loaded model with ultralytics", "SUCCESS")
            except (ImportError, ModuleNotFoundError) as e:
                self.logger.info(f"Ultralytics not available: {e}. Falling back to torch.hub")
            except Exception as e:
                self.logger.warning(f"Ultralytics loading failed: {e}. Falling back to torch.hub")
            
            # Fall back to torch.hub if ultralytics failed
            if not model_loaded:
                try:
                    # Try loading with torch.hub (set trust_repo=True to avoid confirmation)
                    self.logger.info("Loading YOLOv5 model via torch.hub...")
                    self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', 
                                              device=self.device, trust_repo=True)
                    self.model_type = 'torch_hub'
                    model_loaded = True
                    log_system_event(self.logger, "Loaded model with torch.hub", "SUCCESS")
                except Exception as e:
                    self.logger.error(f"torch.hub loading failed: {e}")
                    
                    # Final fallback: create a dummy detector for testing
                    self.logger.warning("Creating dummy detector for testing purposes")
                    self.model = DummyYOLOModel()
                    self.model_type = 'dummy'
                    model_loaded = True
                    log_system_event(self.logger, "Created dummy detector", "WARNING")
            
            if not model_loaded:
                raise RuntimeError("Failed to load YOLO model with any method")
            
            # Set model parameters
            if hasattr(self.model, 'conf'):
                self.model.conf = self.confidence_threshold
            if hasattr(self.model, 'iou'):
                self.model.iou = self.nms_threshold
            
        except Exception as e:
            log_system_event(self.logger, "Model loading failed", str(e))
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def _download_default_model(self):
        """Download default YOLOv5 model if not found."""
        try:
            self.logger.info(f"Model not found at {self.model_path}, downloading default model...")
            
            # Ensure models directory exists
            models_dir = Path(self.model_path).parent
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Download YOLOv5s model (smallest, fastest)
            model_url = "https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt"
            urllib.request.urlretrieve(model_url, self.model_path)
            
            log_system_event(self.logger, "Downloaded default YOLOv5 model", "SUCCESS")
            
        except Exception as e:
            log_system_event(self.logger, "Model download failed", str(e))
            raise
    
    def detect_persons(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect persons in a video frame.
        
        Args:
            frame (np.ndarray): Input video frame
            
        Returns:
            List of detection dictionaries with bounding boxes and confidence scores
        """
        if self.model is None:
            return []
        
        try:
            # Run inference
            if self.model_type == 'ultralytics':
                results = self.model(frame, verbose=False)
                detections = self._parse_ultralytics_results(results)
            else:
                results = self.model(frame)
                detections = self._parse_torch_hub_results(results)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            return []
    
    def _parse_ultralytics_results(self, results) -> List[Dict[str, Any]]:
        """Parse results from ultralytics YOLO format."""
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    # Get box coordinates, confidence, and class
                    box = boxes.xyxy[i].cpu().numpy()  # x1, y1, x2, y2
                    confidence = float(boxes.conf[i].cpu().numpy())
                    class_id = int(boxes.cls[i].cpu().numpy())
                    
                    # Only keep person detections
                    if class_id == self.person_class_id and confidence >= self.confidence_threshold:
                        x1, y1, x2, y2 = box
                        
                        detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'confidence': confidence,
                            'class_id': class_id,
                            'center': (int((x1 + x2) / 2), int((y1 + y2) / 2)),
                            'area': (x2 - x1) * (y2 - y1)
                        })
        
        return detections
    
    def _parse_torch_hub_results(self, results) -> List[Dict[str, Any]]:
        """Parse results from torch.hub YOLOv5 format."""
        detections = []
        
        # Results are in pandas DataFrame format
        df = results.pandas().xyxy[0]
        
        for _, row in df.iterrows():
            # Only keep person detections
            if row['class'] == self.person_class_id and row['confidence'] >= self.confidence_threshold:
                x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                
                detections.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float(row['confidence']),
                    'class_id': int(row['class']),
                    'center': (int((x1 + x2) / 2), int((y1 + y2) / 2)),
                    'area': (x2 - x1) * (y2 - y1)
                })
        
        return detections
    
    def filter_detections(self, detections: List[Dict], min_area: int = 500, 
                         max_area: int = None) -> List[Dict]:
        """
        Filter detections based on size and other criteria.
        
        Args:
            detections (List[Dict]): List of detection dictionaries
            min_area (int): Minimum bounding box area
            max_area (int): Maximum bounding box area
            
        Returns:
            Filtered list of detections
        """
        filtered = []
        
        for detection in detections:
            area = detection['area']
            
            # Filter by area
            if area < min_area:
                continue
            
            if max_area and area > max_area:
                continue
            
            # Additional filters can be added here
            # e.g., aspect ratio, position, etc.
            
            filtered.append(detection)
        
        return filtered
    
    def get_detection_centers(self, detections: List[Dict]) -> List[Tuple[int, int]]:
        """
        Extract center points from detections.
        
        Args:
            detections (List[Dict]): List of detection dictionaries
            
        Returns:
            List of (x, y) center coordinates
        """
        return [detection['center'] for detection in detections]
    
    def update_confidence_threshold(self, new_threshold: float):
        """
        Update confidence threshold.
        
        Args:
            new_threshold (float): New confidence threshold (0.0 - 1.0)
        """
        self.confidence_threshold = new_threshold
        if hasattr(self.model, 'conf'):
            self.model.conf = new_threshold
        log_system_event(self.logger, f"Updated confidence threshold to {new_threshold}")
    
    def update_nms_threshold(self, new_threshold: float):
        """
        Update NMS (Non-Maximum Suppression) threshold.
        
        Args:
            new_threshold (float): New NMS threshold (0.0 - 1.0)
        """
        self.nms_threshold = new_threshold
        if hasattr(self.model, 'iou'):
            self.model.iou = new_threshold
        log_system_event(self.logger, f"Updated NMS threshold to {new_threshold}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'model_path': self.model_path,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'nms_threshold': self.nms_threshold,
            'model_type': getattr(self, 'model_type', 'unknown'),
            'model_loaded': self.model is not None
        }
        
        if self.model:
            try:
                if hasattr(self.model, 'names'):
                    info['class_names'] = self.model.names
                if hasattr(self.model, 'nc'):
                    info['num_classes'] = self.model.nc
            except:
                pass
        
        return info
    
    def benchmark(self, frame: np.ndarray, num_runs: int = 10) -> Dict[str, float]:
        """
        Benchmark detection performance.
        
        Args:
            frame (np.ndarray): Test frame
            num_runs (int): Number of benchmark runs
            
        Returns:
            Dictionary with performance metrics
        """
        import time
        
        times = []
        
        for _ in range(num_runs):
            start_time = time.time()
            detections = self.detect_persons(frame)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = np.mean(times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        return {
            'avg_inference_time': avg_time,
            'fps': fps,
            'min_time': np.min(times),
            'max_time': np.max(times),
            'std_time': np.std(times)
        }


def create_detector(model_path: str = None, device: str = None) -> PersonDetector:
    """
    Factory function to create a PersonDetector instance.
    
    Args:
        model_path (str): Path to YOLO model file
        device (str): Device to run inference on
        
    Returns:
        PersonDetector instance
    """
    return PersonDetector(model_path=model_path, device=device)