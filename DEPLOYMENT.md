# 🚀 Deployment Guide - Crowd Monitoring System

## 📋 Quick Start (5 Minutes)

### 1. **Clone Repository**
```bash
git clone https://github.com/yourusername/crowd-monitoring-system.git
cd crowd-monitoring-system
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Configure for Your Camera**
```bash
# For laptop camera (recommended)
python laptop_config.py

# Or test camera manually
python test_camera.py
```

### 4. **Run System**
```bash
# Counter only
python run.py counter

# Full system with web dashboard
python run.py full

# Web dashboard only
python run.py dashboard
```

### 5. **Access Web Dashboard**
Open browser: `http://localhost:5000`

---

## 🎯 Camera Setup Options

### **Option 1: Laptop Camera (Easiest)**
```bash
python laptop_config.py  # Auto-configures for laptop camera
python run.py counter     # Start monitoring
```

### **Option 2: DroidCam (Phone Camera)**
1. Install DroidCam on phone and PC
2. Connect both to same WiFi
3. Run: `python find_droidcam.py`
4. Update `.env` with new camera index
5. Run: `python run.py counter`

### **Option 3: External USB Camera**
1. Connect USB camera
2. Run: `python test_camera.py`
3. Note camera index
4. Update `CAMERA_SOURCE=X` in `.env`
5. Run: `python run.py counter`

---

## ⚙️ Configuration

### **Basic Settings (.env file):**
```env
CAMERA_SOURCE=0              # Camera index
CONFIDENCE_THRESHOLD=0.4     # Detection sensitivity
CROWD_LIMIT=50              # Maximum people allowed
FLASK_PORT=5000             # Web dashboard port
```

### **Advanced Settings (utils/config.py):**
- Detection line position
- Movement thresholds
- Alert preferences
- Display options

---

## 🎮 Controls

### **Video Window:**
- `q` - Quit application
- `r` - Reset all counts
- `s` - Save screenshot
- `h` - Toggle help display
- `SPACE` - Pause/Resume
- `X button` - Close window

### **Web Dashboard:**
- Real-time monitoring
- Historical reports
- Admin controls
- Configuration settings

---

## 📊 Usage Instructions

### **For Accurate Counting:**
1. **Position camera** to see entry/exit area clearly
2. **People must cross center line** of camera view
3. **Right to Left movement** = Entry (count increases)
4. **Left to Right movement** = Exit (count decreases)
5. **Move slowly** for best detection accuracy

### **Optimal Setup:**
- Camera height: 6-8 feet
- Clear view of pathway
- Good lighting
- Minimal background movement
- Single-file crossing preferred

---

## 🔧 Troubleshooting

### **No Detection:**
- Check camera is working: `python test_camera.py`
- Ensure good lighting
- Lower confidence threshold in `.env`

### **No Counting:**
- People must cross center line of frame
- Move more dramatically (left to right sides)
- Check console for debug messages

### **Poor Performance:**
- Close other applications using camera
- Reduce frame resolution in config
- Check CPU usage

### **Web Dashboard Issues:**
- Check port 5000 is available
- Try different port in `.env`
- Restart system: `python run.py full`

---

## 📈 Production Deployment

### **For Permanent Installation:**
1. **Set up dedicated computer** (laptop/mini PC)
2. **Position camera** for optimal coverage
3. **Configure autostart** (Windows startup/Linux systemd)
4. **Set up remote access** (VPN/port forwarding)
5. **Schedule regular backups** of database
6. **Monitor system health** via web dashboard

### **Security Considerations:**
- Change default Flask secret key
- Use HTTPS for remote access
- Implement user authentication
- Regular security updates

### **Scaling:**
- Multiple cameras: Run separate instances
- Central monitoring: Database synchronization
- Load balancing: Multiple processing nodes

---

## 📁 File Structure

```
crowd-monitoring-system/
├── src/                    # Core application
├── utils/                  # Utilities and config
├── data/                   # Database and reports
├── logs/                   # System logs
├── models/                 # AI models
├── requirements.txt        # Dependencies
├── .env                   # Configuration
├── run.py                 # Main launcher
└── README.md              # Documentation
```

---

## 🆘 Support

### **Common Issues:**
1. **Camera not found** → Run `python test_camera.py`
2. **No counting** → Ensure crossing center line
3. **Poor accuracy** → Adjust lighting and positioning
4. **Web dashboard error** → Check port availability

### **Getting Help:**
- Check documentation files
- Review console output for errors
- Test with `python run.py check`
- Create GitHub issue with details

---

## ✅ System Requirements

### **Minimum:**
- Python 3.8+
- 4GB RAM
- Webcam or phone camera
- Windows/Linux/macOS

### **Recommended:**
- Python 3.10+
- 8GB RAM
- Dedicated USB camera
- SSD storage
- Stable internet (for model downloads)

---

**🎯 The system is ready for production use!**