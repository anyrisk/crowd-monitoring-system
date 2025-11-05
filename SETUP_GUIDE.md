# Complete Setup and Operation Guide

## 📱 Step 1: DroidCam Setup

### Install DroidCam:
1. **On your phone**: Download "DroidCam" from Google Play Store or App Store
2. **On your PC**: Download DroidCam Client from https://www.dev47apps.com/droidcam/windows/
3. **Install both applications**

### Connect Phone Camera:
1. **Connect both devices to same WiFi network**
2. **Open DroidCam on your phone** - note the IP address shown (e.g., 192.168.1.100)
3. **Open DroidCam Client on PC**
4. **Enter the IP address** from your phone
5. **Click "Start"** - you should see your phone's camera feed on PC
6. **Note the camera index** - usually appears as camera index 1 or 2 (not 0)

### Test Camera Connection:
```python
# Quick test script to find your camera index
import cv2

for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"Camera {i}: Working - Resolution: {frame.shape}")
            cv2.imshow(f'Camera {i}', frame)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```