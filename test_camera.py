#!/usr/bin/env python3
"""
Camera Test Script - Find and test your DroidCam connection
"""

import cv2
import sys

def test_cameras():
    """Test all available camera indices to find DroidCam."""
    print("🔍 Scanning for available cameras...")
    print("=" * 50)
    
    working_cameras = []
    
    for i in range(10):  # Test indices 0-9
        print(f"Testing camera index {i}...", end=" ")
        
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            # Try to read a frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ WORKING - Resolution: {width}x{height}")
                working_cameras.append({
                    'index': i,
                    'width': width,
                    'height': height
                })
                
                # Show preview for 2 seconds
                cv2.imshow(f'Camera {i} Preview', frame)
                cv2.waitKey(2000)
                cv2.destroyAllWindows()
            else:
                print("❌ Can't read frames")
        else:
            print("❌ Can't open")
        
        cap.release()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    if working_cameras:
        print(f"Found {len(working_cameras)} working camera(s):")
        for cam in working_cameras:
            print(f"  • Camera {cam['index']}: {cam['width']}x{cam['height']}")
        
        print(f"\n💡 Recommended: Use camera index {working_cameras[0]['index']} for DroidCam")
        print(f"   Update your .env file: CAMERA_SOURCE={working_cameras[0]['index']}")
        
        return working_cameras[0]['index']
    else:
        print("❌ No working cameras found!")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure DroidCam is running on both phone and PC")
        print("2. Check if both devices are on same WiFi network")
        print("3. Try restarting DroidCam applications")
        return None

def live_camera_test(camera_index):
    """Test camera with live preview."""
    print(f"\n🎥 Testing camera {camera_index} with live preview...")
    print("Press 'q' to quit, 's' to save screenshot")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_index}")
        return False
    
    # Set camera properties for better quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
        
        frame_count += 1
        
        # Add frame info overlay
        cv2.putText(frame, f"Camera {camera_index} - Frame: {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save screenshot", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow(f'Camera {camera_index} Live Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"camera_test_screenshot_{camera_index}.jpg"
            cv2.imwrite(filename, frame)
            print(f"📸 Screenshot saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Camera test completed")
    return True

if __name__ == "__main__":
    print("🎯 DroidCam Camera Detection and Test Tool")
    print("=" * 50)
    
    # First, scan for cameras
    camera_index = test_cameras()
    
    if camera_index is not None:
        # Ask user if they want to do live test
        response = input(f"\n🎥 Do you want to test camera {camera_index} with live preview? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            live_camera_test(camera_index)
        
        print(f"\n✅ Setup complete! Use camera index {camera_index} in your configuration.")
    else:
        print("\n❌ Setup failed. Please check your DroidCam connection.")
        sys.exit(1)