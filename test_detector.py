#!/usr/bin/env python3
"""
Simple test script for the detector module.
Tests if the detector can load and work without ultralytics.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_detector():
    """Test the detector module."""
    print("Testing PersonDetector...")
    
    try:
        from src.detector import create_detector
        print("✅ Successfully imported detector module")
        
        # Create detector instance
        detector = create_detector()
        print("✅ Successfully created detector instance")
        
        # Get model info
        model_info = detector.get_model_info()
        print(f"✅ Model info: {model_info['model_type']}")
        print(f"   Device: {model_info['device']}")
        print(f"   Model loaded: {model_info['model_loaded']}")
        
        # Create a test frame (dummy image)
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        print("✅ Created test frame")
        
        # Test detection
        detections = detector.detect_persons(test_frame)
        print(f"✅ Detection test completed - found {len(detections)} persons")
        
        # Test benchmark (quick test with 3 runs)
        print("Running quick benchmark...")
        benchmark = detector.benchmark(test_frame, num_runs=3)
        print(f"✅ Benchmark completed - Average FPS: {benchmark['fps']:.2f}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_system_requirements():
    """Test system requirements."""
    print("\nTesting system requirements...")
    
    # Test torch
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch not installed")
        return False
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV not installed")
        return False
    
    # Test ultralytics (optional)
    try:
        import ultralytics
        print(f"✅ Ultralytics {ultralytics.__version__} (optional)")
    except ImportError:
        print("⚠️  Ultralytics not installed (will use torch.hub fallback)")
    
    return True

def main():
    """Main test function."""
    print("=" * 50)
    print("Crowd Monitor Detector Test")
    print("=" * 50)
    
    # Test requirements
    if not test_system_requirements():
        print("\n❌ System requirements not met")
        return False
    
    # Test detector
    if not test_detector():
        print("\n❌ Detector test failed")
        return False
    
    print("\n✅ All tests passed! The detector is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)