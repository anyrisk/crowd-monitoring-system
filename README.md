# Crowd Monitoring System

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green)
![YOLOv5](https://img.shields.io/badge/YOLOv5-Latest-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

🏛️ **A comprehensive real-time people counting system for temples and religious spaces using AI-powered computer vision.**

This system provides accurate entry/exit counting, crowd management, analytics, and web dashboard monitoring using Python, OpenCV, and YOLO object detection.

## 🎯 Features
- Real-time human detection using YOLOv5
- Entry/Exit counting with virtual line detection
- Live headcount display with video overlay
- SQLite database logging with timestamps
- Daily/weekly/monthly visitor reports
- Crowd limit alerts and safety notifications
- Optional web dashboard for monitoring

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python src/main.py
   ```

3. **Access Dashboard (Optional)**
   ```
   http://localhost:5000/
   ```

## 📁 Project Structure

```
temple_project/
├── src/                 # Main application code
│   ├── main.py         # Entry point
│   ├── detector.py     # YOLO human detection
│   ├── tracker.py      # Object tracking
│   ├── counter.py      # Line-crossing logic
│   ├── overlay.py      # Video overlays
│   ├── alerts.py       # Alert system
│   ├── database.py     # Database operations
│   ├── reports.py      # Report generation
│   ├── dashboard.py    # Web dashboard
│   └── admin.py        # Admin controls
├── utils/              # Utility modules
│   ├── config.py       # Configuration
│   ├── logger.py       # Logging utilities
│   └── draw_utils.py   # Drawing helpers
├── data/               # Data storage
│   ├── database.db     # SQLite database
│   └── reports/        # Generated reports
├── models/             # YOLO model files
└── requirements.txt    # Dependencies
```

## ⚙️ Configuration

Edit `utils/config.py` to customize:
- Camera settings
- Detection line position
- Crowd limit thresholds
- Database path
- Alert preferences

## 📊 Usage

1. **Live Monitoring**: The main application shows real-time video with people detection
2. **Count Tracking**: Virtual line detects entries/exits automatically
3. **Data Logging**: All events are stored in SQLite database
4. **Reports**: Generate visitor summaries and export to CSV/Excel
5. **Alerts**: Get notified when crowd limits are exceeded

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenCV** - Video processing
- **YOLOv5** - Human detection
- **DeepSORT** - Object tracking
- **SQLite** - Database storage
- **Flask/Streamlit** - Web dashboard
- **Pandas** - Data analysis

## 📈 Reports

Generate reports with:
```python
from src.reports import ReportGenerator
generator = ReportGenerator()
generator.generate_daily_report(date="2024-01-15")
generator.export_to_csv("daily_visitors.csv")
```

## 🚨 Safety Features

- Real-time crowd monitoring
- Configurable capacity limits
- Visual and audio alerts
- Emergency count reset
- Historical trend analysis

## 📞 Support

For issues and feature requests, please check the documentation or create an issue.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [YOLOv5](https://github.com/ultralytics/yolov5) for object detection
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [Flask](https://flask.palletsprojects.com/) for web framework
- The open-source community for inspiration and tools

## 📧 Contact

Project Link: [https://github.com/anyrisk/crowd-monitoring-system](https://github.com/anyrisk/crowd-monitoring-system)

---

**Crowd Monitoring System** - Smart visitor management with AI-powered analytics.
