#!/usr/bin/env python3
"""
Temple People Counter - Main startup script.
Provides options to run the system in different modes.
"""

import sys
import argparse
import threading
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from src.main import create_temple_counter
    from src.dashboard import create_dashboard_server
    from utils.config import get_config
    from utils.logger import default_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def run_counter_only():
    """Run only the people counter without web dashboard."""
    print("Starting Temple People Counter (Counter Only Mode)")
    print("Press 'q' to quit, 'r' to reset counts, 's' to save screenshot")
    print("-" * 60)
    
    try:
        counter = create_temple_counter()
        counter.run()
    except KeyboardInterrupt:
        print("\nCounter stopped by user")
    except Exception as e:
        print(f"Error running counter: {e}")


def run_with_dashboard():
    """Run people counter with web dashboard."""
    print("Starting Temple People Counter (Full System Mode)")
    print("Web dashboard will be available at http://localhost:5000")
    print("Press Ctrl+C to stop both services")
    print("-" * 60)
    
    config = get_config()
    
    try:
        # Start web dashboard in background thread
        dashboard = create_dashboard_server()
        dashboard_thread = dashboard.start_server(threaded=True)
        
        print(f"Dashboard server started at http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        time.sleep(2)  # Give dashboard time to start
        
        # Start people counter in main thread
        counter = create_temple_counter()
        
        print("Starting video processing...")
        counter.run()
        
    except KeyboardInterrupt:
        print("\nStopping services...")
        if 'dashboard' in locals():
            dashboard.stop_server()
    except Exception as e:
        print(f"Error running system: {e}")


def run_dashboard_only():
    """Run only the web dashboard for monitoring."""
    print("Starting Temple People Counter (Dashboard Only Mode)")
    print("Web dashboard will be available at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        dashboard = create_dashboard_server()
        dashboard.start_server(threaded=False)  # Run in main thread
    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"Error running dashboard: {e}")


def check_system():
    """Check system configuration and dependencies."""
    print("Temple People Counter - System Check")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("⚠️  Warning: Python 3.8+ recommended")
    else:
        print("✅ Python version OK")
    
    # Check dependencies
    required_modules = [
        ('cv2', 'opencv-python'),
        ('torch', 'torch'),
        ('ultralytics', 'ultralytics'),
        ('pandas', 'pandas'),
        ('matplotlib', 'matplotlib'),
        ('sqlite3', 'built-in'),
        ('flask', 'flask (optional for dashboard)'),
    ]
    
    print("\nDependency Check:")
    missing_modules = []
    
    for module, package in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (install: pip install {package})")
            if package != 'built-in' and 'optional' not in package:
                missing_modules.append(package)
    
    # Check configuration
    print("\nConfiguration Check:")
    try:
        config = get_config()
        print(f"✅ Configuration loaded")
        print(f"   - Camera Source: {config.CAMERA_SOURCE}")
        print(f"   - YOLO Model: {config.YOLO_MODEL_PATH}")
        print(f"   - Crowd Limit: {config.CROWD_LIMIT}")
        print(f"   - Database: {config.DATABASE_PATH}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Check directories
    print("\nDirectory Check:")
    directories = [
        project_root / "data",
        project_root / "models",
        project_root / "logs",
        project_root / "reports"
    ]
    
    for directory in directories:
        if directory.exists():
            print(f"✅ {directory.name}/")
        else:
            print(f"⚠️  {directory.name}/ (will be created)")
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {directory.name}/")
    
    print("\nSystem Status:")
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ System ready to run!")
        return True


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Temple People Counter System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Operating Modes:
  counter    - Run people counter only (no web interface)
  dashboard  - Run web dashboard only (for monitoring existing data)
  full       - Run both counter and dashboard (recommended)
  check      - Check system configuration and dependencies

Examples:
  python run.py counter           # Counter only
  python run.py full             # Full system with dashboard
  python run.py dashboard        # Dashboard only
  python run.py check            # System check

Controls (Counter Mode):
  'q' - Quit application
  'r' - Reset all counts
  's' - Save screenshot
  'h' - Toggle help display
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['counter', 'dashboard', 'full', 'check'],
        help='Operating mode'
    )
    
    parser.add_argument(
        '--host',
        default='localhost',
        help='Dashboard host address (default: localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Dashboard port number (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'check':
        success = check_system()
        sys.exit(0 if success else 1)
    
    elif args.mode == 'counter':
        run_counter_only()
    
    elif args.mode == 'dashboard':
        # Update config for custom host/port
        if args.host != 'localhost' or args.port != 5000:
            import os
            os.environ['FLASK_HOST'] = args.host
            os.environ['FLASK_PORT'] = str(args.port)
        
        run_dashboard_only()
    
    elif args.mode == 'full':
        # Update config for custom host/port
        if args.host != 'localhost' or args.port != 5000:
            import os
            os.environ['FLASK_HOST'] = args.host
            os.environ['FLASK_PORT'] = str(args.port)
        
        run_with_dashboard()


if __name__ == "__main__":
    main()