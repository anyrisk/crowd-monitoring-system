#!/usr/bin/env python3
"""
Quick script to find DroidCam after setup
"""

import cv2

print("🔍 Looking for DroidCam camera...")
print("Make sure DroidCam is connected and running!")
print("=" * 50)

for i in range(5):
    print(f"Testing camera {i}...", end=" ")
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"✅ Found camera - Resolution: {w}x{h}")
            
            # Show preview
            cv2.imshow(f'Camera {i}', frame)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
        else:
            print("❌ Can't read")
    else:
        print("❌ Not available")
    
    cap.release()

print("\n💡 After setting up DroidCam, update your .env file:")
print("   CAMERA_SOURCE=X  (where X is your DroidCam camera index)")