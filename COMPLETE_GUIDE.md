# 🎯 Complete Crowd Monitoring System Guide

## 📋 Prerequisites Checklist
- [ ] Windows PC
- [ ] Android/iOS phone with camera
- [ ] Both devices on same WiFi network
- [ ] Python 3.8+ installed

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you get errors, install individually:
pip install opencv-python opencv-contrib-python
pip install torch torchvision ultralytics
pip install pandas numpy matplotlib seaborn
pip install flask plotly xlsxwriter openpyxl
pip install python-dotenv pillow tqdm plyer pygame
```

### Step 2: Setup DroidCam
1. **Download DroidCam:**
   - Phone: Install "DroidCam" from app store
   - PC: Download from https://www.dev47apps.com/droidcam/windows/

2. **Connect Camera:**
   - Open DroidCam on phone (note the IP address)
   - Open DroidCam Client on PC
   - Enter phone's IP address and click "Start"

3. **Test Camera Connection:**
```bash
python test_camera.py
```

### Step 3: Configure System
1. **Update Camera Source:**
   - Edit `.env` file
   - Set `CAMERA_SOURCE=X` (where X is your camera index from test)

2. **Configure Detection Line:**
   - Edit `utils/config.py`
   - Adjust `COUNTING_LINE` coordinates for your setup

### Step 4: First Run
```bash
# Check system status
python run.py check

# Run counter only (no web dashboard)
python run.py counter

# Run full system with web dashboard
python run.py full
```

## 🎮 Operating the System

### Basic Controls (Video Window)
- **'q'** - Quit application
- **'r'** - Reset all counts
- **'s'** - Save screenshot
- **'h'** - Toggle help display

### Web Dashboard Access
- Open browser: `http://localhost:5000`
- Real-time monitoring and controls
- Historical data and reports

## 🔧 Configuration Guide

### Camera Settings (`utils/config.py`)
```python
# Camera configuration
CAMERA_SOURCE = 1  # Your DroidCam index
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30
```

### Detection Line Setup
```python
# Counting line (as percentage of frame)
COUNTING_LINE = {
    "start": (0.3, 0.5),  # Left side (30% from left, 50% from top)
    "end": (0.7, 0.5),    # Right side (70% from left, 50% from top)
    "thickness": 3,
    "color": (0, 255, 0)  # Green line
}
```

### Crowd Limits
```python
CROWD_LIMIT = 50  # Maximum people allowed
WARNING_THRESHOLD = 40  # 80% of limit (warning alert)
```

## 📊 Using Features

### 1. Live Monitoring
- **Video Feed**: Shows real-time camera with detection boxes
- **Statistics Overlay**: Current count, entries, exits
- **Detection Line**: Green line showing counting boundary

### 2. Database Logging
- **Automatic**: Every entry/exit logged with timestamp
- **Location**: `data/database.db`
- **View Data**: Use web dashboard or database tools

### 3. Reports Generation
```python
# Generate reports programmatically
from src.reports import ReportGenerator

generator = ReportGenerator()

# Daily report
daily_report = generator.generate_daily_report()
generator.export_to_csv("daily_report.csv")

# Weekly report
weekly_report = generator.generate_weekly_report()
generator.export_to_excel("weekly_report.xlsx")

# Monthly report
monthly_report = generator.generate_monthly_report()
```

### 4. Web Dashboard Features
- **Live View**: Real-time statistics and camera feed
- **Historical Data**: Charts and trends
- **Reports**: Generate and download reports
- **Admin Panel**: Reset counts, configure settings
- **Alerts**: View and manage crowd limit notifications

### 5. Alert System
- **Visual Alerts**: On-screen notifications
- **Sound Alerts**: Audio warnings (if enabled)
- **System Notifications**: Desktop notifications
- **Configurable**: Set custom thresholds

## 🎯 Positioning Your Setup

### Optimal Camera Placement
1. **Height**: 8-10 feet above ground
2. **Angle**: Slight downward angle (15-30 degrees)
3. **Coverage**: Clear view of entry/exit area
4. **Lighting**: Avoid backlighting, ensure good illumination

### Detection Line Positioning
1. **Location**: Across the entry/exit pathway
2. **Direction**: Perpendicular to people flow
3. **Clear Area**: No obstructions crossing the line
4. **Single File**: Best results when people cross one at a time

## 🔍 Verification and Testing

### Test Scenarios
1. **Single Person Entry**: Walk across line (entry direction)
2. **Single Person Exit**: Walk across line (exit direction)
3. **Multiple People**: Test with 2-3 people
4. **Edge Cases**: Test partial crossings, stopping on line

### Verification Checklist
- [ ] Camera feed is clear and stable
- [ ] Detection boxes appear around people
- [ ] Counting line is visible and positioned correctly
- [ ] Entry count increases when crossing entry direction
- [ ] Exit count increases when crossing exit direction
- [ ] Current count = Entries - Exits
- [ ] Database logs show correct timestamps
- [ ] Web dashboard displays real-time data
- [ ] Reports generate correctly
- [ ] Alerts trigger at configured thresholds

## 🚨 Troubleshooting

### Common Issues
1. **Camera Not Found**: Run `python test_camera.py` again
2. **Poor Detection**: Adjust lighting or camera angle
3. **Wrong Counts**: Reconfigure detection line position
4. **Web Dashboard Not Loading**: Check if port 5000 is available
5. **Model Download Fails**: Check internet connection

### Performance Optimization
1. **Lower Resolution**: Reduce FRAME_WIDTH/HEIGHT for better FPS
2. **Adjust Confidence**: Lower CONFIDENCE_THRESHOLD for more detections
3. **GPU Acceleration**: Set DEVICE='cuda' if you have NVIDIA GPU

## 📈 Best Practices

### Daily Operation
1. **Start System**: `python run.py full`
2. **Monitor Dashboard**: Check `http://localhost:5000`
3. **Verify Counts**: Cross-check with manual observations
4. **Generate Reports**: Daily summary at end of day
5. **Backup Data**: Regular database backups

### Maintenance
1. **Clean Camera Lens**: Keep phone camera clean
2. **Check Positioning**: Ensure camera hasn't moved
3. **Update Thresholds**: Adjust based on actual usage patterns
4. **Review Logs**: Check for any error messages
5. **Test Alerts**: Verify notification system works

This guide covers everything you need to successfully operate your crowd monitoring system!