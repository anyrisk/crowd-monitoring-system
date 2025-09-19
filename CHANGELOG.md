# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-19

### Added
- Initial release of Crowd Monitoring System
- Real-time people detection using YOLOv5
- Entry/exit counting with line-crossing detection
- Centroid-based object tracking across video frames
- SQLite database for comprehensive event logging
- Flask web dashboard with live monitoring
- Administrative controls and system management
- Alert system for crowd limit monitoring
- Analytics and report generation (CSV/Excel export)
- Multi-mode operation (counter, dashboard, full system)
- Configurable crowd limits and detection parameters
- Keyboard controls for real-time interaction
- Comprehensive logging and error handling
- Docker deployment support preparation
- Complete documentation and setup guides

### Features
- **Core Detection**: YOLOv5-powered human detection
- **Tracking**: Centroid-based multi-object tracking
- **Counting**: Geometric line-crossing analysis
- **Database**: SQLite with event history and statistics
- **Web Interface**: Real-time dashboard with admin panel
- **Analytics**: Historical data analysis and visualization
- **Alerts**: Configurable crowd limit notifications
- **Reports**: Automated CSV/Excel report generation
- **Configuration**: Environment-based settings management
- **Deployment**: Multiple running modes for different use cases

### Technical Stack
- Python 3.8+
- OpenCV 4.8+
- YOLOv5/Ultralytics
- Flask web framework
- SQLite database
- Pandas for data analysis
- Matplotlib for visualization
- Threading for concurrent operations

### Supported Platforms
- Windows 10/11
- Linux (Ubuntu 18.04+)
- macOS (10.15+)

## [Unreleased]

### Planned Features
- Docker containerization
- REST API endpoints
- User authentication system
- Multi-camera support
- Cloud storage integration
- Mobile app companion
- Advanced analytics dashboard
- Machine learning model training tools