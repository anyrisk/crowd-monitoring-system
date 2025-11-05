# 🎯 Testing Your Crowd Monitoring System

## What You Should See Right Now

### Video Window
- **Camera Feed**: Live video from your camera (index 0)
- **Green Bounding Boxes**: Around detected people
- **Yellow Counting Line**: Horizontal line across the middle
- **Statistics Panel**: Top-left corner showing:
  - People Inside: 0
  - Total Entries: 0  
  - Total Exits: 0
  - FPS: ~30
  - Current Time

### Console Output
- System initialization messages
- YOLO model loading (SUCCESS)
- Camera initialization (1280x720 @ 30fps)
- Control instructions

## 🧪 Testing Steps

### Step 1: Basic Detection Test
1. **Move in front of camera** - you should see green boxes around people
2. **Check detection accuracy** - boxes should follow people smoothly
3. **Test multiple people** - if possible, have 2-3 people in view

### Step 2: Counting Line Test
1. **Position yourself** to one side of the yellow counting line
2. **Cross the line slowly** from left to right (should count as entry)
3. **Watch the statistics** - "Total Entries" should increase by 1
4. **Cross back** from right to left (should count as exit)
5. **Check "Total Exits"** - should increase by 1
6. **Verify "People Inside"** - should be Entries - Exits

### Step 3: Controls Test
- **Press 'h'** - Toggle help display (shows controls on screen)
- **Press 's'** - Save screenshot (check for saved file)
- **Press 'r'** - Reset all counts to zero
- **Press 'SPACE'** - Pause video (press any key to resume)
- **Press 'q'** - Quit application

### Step 4: Performance Test
- **Check FPS** - should be around 20-30 fps
- **Test with movement** - detection should be smooth
- **Multiple people** - system should handle 2-3 people simultaneously

## 🔧 Troubleshooting

### If No Video Window Appears:
```bash
# Test camera directly
python test_camera.py
```

### If Detection Boxes Don't Appear:
- **Lighting**: Ensure good lighting
- **Distance**: Stand 3-6 feet from camera
- **Movement**: Try moving slowly

### If Counting Doesn't Work:
- **Line Position**: Make sure you cross the yellow line completely
- **Direction**: Try crossing from different directions
- **Speed**: Cross slowly and deliberately

### If FPS is Low:
- **Close other applications** using camera
- **Reduce resolution** in config if needed
- **Check CPU usage**

## 📊 Expected Results

### Good Detection:
- ✅ Green boxes around people
- ✅ Boxes follow movement smoothly
- ✅ FPS above 15
- ✅ Minimal false detections

### Good Counting:
- ✅ Entry count increases when crossing line (one direction)
- ✅ Exit count increases when crossing back
- ✅ People Inside = Entries - Exits
- ✅ No double counting

## 🎯 Next Steps After Basic Test

1. **Test with DroidCam** (your phone camera)
2. **Configure detection line position**
3. **Set up web dashboard**
4. **Test alert system**
5. **Generate reports**

## 📱 Setting Up DroidCam (Next Phase)

Once basic testing works:

1. **Install DroidCam** on phone and PC
2. **Connect both to same WiFi**
3. **Run**: `python find_droidcam.py`
4. **Update .env**: Set `CAMERA_SOURCE=X` (new camera index)
5. **Test again**: `python run.py counter`

## 🌐 Web Dashboard (After Camera Setup)

```bash
# Run full system with web dashboard
python run.py full

# Open browser to: http://localhost:5000
```

## 📈 Report Generation

```bash
# Generate daily report
python -c "from src.reports import ReportGenerator; r=ReportGenerator(); r.generate_daily_report()"
```

Let me know what you see and any issues you encounter!