#!/usr/bin/env python3
"""
System Performance Benchmark Tool
Tests and measures system performance metrics
"""

import time
import cv2
import numpy as np
from datetime import datetime
import statistics

def benchmark_camera_performance(camera_index=0, duration=30):
    """Benchmark camera capture performance."""
    print(f"🎥 Benchmarking camera {camera_index} for {duration} seconds...")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_index}")
        return None
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_times = []
    frame_count = 0
    start_time = time.time()
    
    while time.time() - start_time < duration:
        frame_start = time.time()
        ret, frame = cap.read()
        frame_end = time.time()
        
        if ret:
            frame_times.append(frame_end - frame_start)
            frame_count += 1
        else:
            print("⚠️  Failed to read frame")
    
    cap.release()
    
    if frame_times:
        avg_frame_time = statistics.mean(frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        results = {
            'duration': duration,
            'frames_captured': frame_count,
            'average_fps': fps,
            'min_frame_time': min(frame_times),
            'max_frame_time': max(frame_times),
            'avg_frame_time': avg_frame_time
        }
        
        print(f"✅ Camera Performance Results:")
        print(f"   Frames Captured: {frame_count}")
        print(f"   Average FPS: {fps:.1f}")
        print(f"   Frame Time: {avg_frame_time*1000:.1f}ms (avg)")
        print(f"   Frame Time Range: {min(frame_times)*1000:.1f}-{max(frame_times)*1000:.1f}ms")
        
        return results
    
    return None

def benchmark_detection_performance(num_frames=100):
    """Benchmark AI detection performance."""
    print(f"🤖 Benchmarking AI detection with {num_frames} frames...")
    
    try:
        from src.detector import create_detector
        detector = create_detector()
        
        # Create test frames
        test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        
        detection_times = []
        
        for i in range(num_frames):
            start_time = time.time()
            detections = detector.detect_persons(test_frame)
            end_time = time.time()
            
            detection_times.append(end_time - start_time)
            
            if (i + 1) % 20 == 0:
                print(f"   Processed {i + 1}/{num_frames} frames...")
        
        avg_detection_time = statistics.mean(detection_times)
        detection_fps = 1.0 / avg_detection_time if avg_detection_time > 0 else 0
        
        results = {
            'frames_processed': num_frames,
            'avg_detection_time': avg_detection_time,
            'detection_fps': detection_fps,
            'min_detection_time': min(detection_times),
            'max_detection_time': max(detection_times)
        }
        
        print(f"✅ Detection Performance Results:")
        print(f"   Frames Processed: {num_frames}")
        print(f"   Average Detection Time: {avg_detection_time*1000:.1f}ms")
        print(f"   Detection FPS: {detection_fps:.1f}")
        print(f"   Time Range: {min(detection_times)*1000:.1f}-{max(detection_times)*1000:.1f}ms")
        
        return results
        
    except Exception as e:
        print(f"❌ Detection benchmark failed: {e}")
        return None

def benchmark_full_system(duration=60):
    """Benchmark full system performance."""
    print(f"🎯 Benchmarking full system for {duration} seconds...")
    
    try:
        from src.main import CrowdMonitoringSystem
        
        system = CrowdMonitoringSystem()
        
        # Initialize camera
        if not system._initialize_camera():
            print("❌ Failed to initialize camera")
            return None
        
        frame_count = 0
        processing_times = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            ret, frame = system.camera.read()
            
            if ret:
                process_start = time.time()
                processed_frame = system._process_frame(frame)
                process_end = time.time()
                
                processing_times.append(process_end - process_start)
                frame_count += 1
                
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"   Processed {frame_count} frames in {elapsed:.1f}s...")
        
        system._cleanup()
        
        if processing_times:
            avg_processing_time = statistics.mean(processing_times)
            system_fps = 1.0 / avg_processing_time if avg_processing_time > 0 else 0
            
            results = {
                'duration': duration,
                'frames_processed': frame_count,
                'avg_processing_time': avg_processing_time,
                'system_fps': system_fps,
                'min_processing_time': min(processing_times),
                'max_processing_time': max(processing_times)
            }
            
            print(f"✅ Full System Performance Results:")
            print(f"   Frames Processed: {frame_count}")
            print(f"   Average Processing Time: {avg_processing_time*1000:.1f}ms")
            print(f"   System FPS: {system_fps:.1f}")
            print(f"   Processing Range: {min(processing_times)*1000:.1f}-{max(processing_times)*1000:.1f}ms")
            
            return results
        
    except Exception as e:
        print(f"❌ Full system benchmark failed: {e}")
        return None

def run_comprehensive_benchmark():
    """Run comprehensive system benchmark."""
    print("\n🚀 CROWD MONITORING SYSTEM BENCHMARK")
    print("="*50)
    print("This will test camera, detection, and full system performance")
    print("="*50)
    
    results = {}
    
    # Camera benchmark
    print("\n1. Camera Performance Test...")
    camera_results = benchmark_camera_performance(duration=10)
    if camera_results:
        results['camera'] = camera_results
    
    # Detection benchmark
    print("\n2. AI Detection Performance Test...")
    detection_results = benchmark_detection_performance(num_frames=50)
    if detection_results:
        results['detection'] = detection_results
    
    # Full system benchmark
    print("\n3. Full System Performance Test...")
    system_results = benchmark_full_system(duration=30)
    if system_results:
        results['full_system'] = system_results
    
    # Summary
    print("\n" + "="*50)
    print("📊 BENCHMARK SUMMARY")
    print("="*50)
    
    if 'camera' in results:
        print(f"Camera FPS: {results['camera']['average_fps']:.1f}")
    
    if 'detection' in results:
        print(f"Detection FPS: {results['detection']['detection_fps']:.1f}")
    
    if 'full_system' in results:
        print(f"System FPS: {results['full_system']['system_fps']:.1f}")
        
        # Performance rating
        fps = results['full_system']['system_fps']
        if fps >= 20:
            rating = "Excellent ⭐⭐⭐⭐⭐"
        elif fps >= 15:
            rating = "Good ⭐⭐⭐⭐"
        elif fps >= 10:
            rating = "Fair ⭐⭐⭐"
        elif fps >= 5:
            rating = "Poor ⭐⭐"
        else:
            rating = "Very Poor ⭐"
        
        print(f"Performance Rating: {rating}")
    
    print("="*50)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    
    try:
        import json
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {filename}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results

if __name__ == "__main__":
    run_comprehensive_benchmark()