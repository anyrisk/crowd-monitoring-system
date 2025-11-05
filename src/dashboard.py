"""
Web dashboard for the Smart Crowd Monitoring System.
Provides live monitoring and historical data visualization using Flask.
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
import threading
import time
import logging
from pathlib import Path
import os

from utils.config import get_config
from utils.logger import default_logger
from src.database import get_database_manager
from src.admin import create_admin_controller
from src.reports import create_report_generator
from src.alerts import create_alert_manager


class DashboardServer:
    """
    Flask-based web dashboard for the people counter system.
    """
    
    def __init__(self, host: str = None, port: int = None, logger: logging.Logger = None):
        """
        Initialize dashboard server.
        
        Args:
            host (str): Host address to bind to
            port (int): Port number to bind to
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        
        # Server configuration
        self.host = host or self.config.FLASK_HOST
        self.port = port or self.config.FLASK_PORT
        self.debug = self.config.DEBUG_MODE
        
        # Initialize components
        self.db_manager = get_database_manager()
        self.admin_controller = create_admin_controller()
        self.report_generator = create_report_generator()
        self.alert_manager = create_alert_manager()
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.secret_key = 'crowd_monitor_secret_key_2024'  # Change in production
        
        # Live data cache
        self.live_data_cache = {
            'counts': {'count_inside': 0, 'total_entered': 0, 'total_exited': 0},
            'alerts': [],
            'last_update': datetime.now()
        }
        
        # Background thread for data updates
        self.update_thread = None
        self.running = False
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """Get current system status."""
            try:
                status = self.admin_controller.get_system_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/counts')
        def api_counts():
            """Get current people counts."""
            try:
                counts = self.db_manager.get_current_count()
                return jsonify({
                    'success': True,
                    'data': counts,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/daily-stats')
        def api_daily_stats():
            """Get daily statistics."""
            try:
                target_date = request.args.get('date')
                if target_date:
                    target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                else:
                    target_date = date.today()
                
                stats = self.db_manager.get_daily_stats(target_date)
                hourly_data = self.db_manager.get_hourly_distribution(target_date)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'daily_stats': stats,
                        'hourly_breakdown': hourly_data
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/weekly-stats')
        def api_weekly_stats():
            """Get weekly statistics."""
            try:
                start_date = request.args.get('start_date')
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                else:
                    # Default to current week
                    today = date.today()
                    start_date = today - timedelta(days=today.weekday())
                
                # Get daily data for the week
                weekly_data = []
                for i in range(7):
                    current_date = start_date + timedelta(days=i)
                    daily_stats = self.db_manager.get_daily_stats(current_date)
                    daily_stats['date'] = current_date.isoformat()
                    daily_stats['day_name'] = current_date.strftime('%A')
                    weekly_data.append(daily_stats)
                
                return jsonify({
                    'success': True,
                    'data': weekly_data
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Get active alerts."""
            try:
                active_alerts = self.alert_manager.get_active_alerts()
                alert_stats = self.alert_manager.get_alert_statistics()
                
                alerts_data = []
                for alert in active_alerts:
                    alerts_data.append({
                        'type': alert.alert_type.value,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat(),
                        'current_count': alert.current_count,
                        'threshold': alert.threshold
                    })
                
                return jsonify({
                    'success': True,
                    'data': {
                        'active_alerts': alerts_data,
                        'statistics': alert_stats
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/admin/reset-counts', methods=['POST'])
        def api_reset_counts():
            """Reset all counts (admin function)."""
            try:
                data = request.get_json() or {}
                reason = data.get('reason', 'Web dashboard reset')
                admin_user = data.get('admin_user', 'web_admin')
                
                result = self.admin_controller.reset_all_counts(reason, admin_user)
                
                return jsonify({
                    'success': result['success'],
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/admin/update-crowd-limit', methods=['POST'])
        def api_update_crowd_limit():
            """Update crowd limit (admin function)."""
            try:
                data = request.get_json()
                new_limit = data.get('new_limit')
                admin_user = data.get('admin_user', 'web_admin')
                
                if not new_limit or new_limit <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid crowd limit value'
                    }), 400
                
                result = self.admin_controller.update_crowd_limit(new_limit, admin_user)
                
                return jsonify({
                    'success': result['success'],
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/admin/update-alert-settings', methods=['POST'])
        def api_update_alert_settings():
            """Update alert settings (admin function)."""
            try:
                data = request.get_json()
                admin_user = data.get('admin_user', 'web_admin')
                
                result = self.admin_controller.update_alert_settings(
                    alerts_enabled=data.get('alerts_enabled'),
                    sound_alerts=data.get('sound_alerts'),
                    popup_alerts=data.get('popup_alerts'),
                    alert_cooldown=data.get('alert_cooldown'),
                    admin_user=admin_user
                )
                
                return jsonify({
                    'success': result['success'],
                    'data': result
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/reports/generate', methods=['POST'])
        def api_generate_report():
            """Generate and download report."""
            try:
                data = request.get_json()
                report_type = data.get('report_type', 'daily')
                target_date_str = data.get('target_date')
                format_type = data.get('format', 'csv')
                admin_user = data.get('admin_user', 'web_admin')
                
                # Parse target date
                if target_date_str:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
                else:
                    target_date = date.today()
                
                # Generate report
                result = self.admin_controller.generate_system_report(
                    report_type, target_date, admin_user
                )
                
                if result['success']:
                    file_path = result['files'].get(format_type)
                    if file_path and os.path.exists(file_path):
                        return jsonify({
                            'success': True,
                            'data': {
                                'download_url': f'/api/reports/download?file={os.path.basename(file_path)}',
                                'filename': os.path.basename(file_path)
                            }
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Report file not found'
                        }), 404
                else:
                    return jsonify({
                        'success': False,
                        'error': result.get('error', 'Report generation failed')
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/reports/download')
        def api_download_report():
            """Download generated report file."""
            try:
                filename = request.args.get('file')
                if not filename:
                    return jsonify({'error': 'No file specified'}), 400
                
                file_path = self.config.REPORTS_DIR / filename
                
                if not file_path.exists():
                    return jsonify({'error': 'File not found'}), 404
                
                return send_file(file_path, as_attachment=True)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/admin')
        def admin_page():
            """Admin control page."""
            return render_template('admin.html')
        
        @self.app.route('/reports')
        def reports_page():
            """Reports page."""
            return render_template('reports.html')
    
    def create_templates(self):
        """Create basic HTML templates if they don't exist."""
        templates_dir = Path(__file__).parent / 'templates'
        templates_dir.mkdir(exist_ok=True)
        
        # Main dashboard template
        dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crowd Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #666; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 4px; }
        .alert-warning { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
        .alert-danger { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-danger { background-color: #e74c3c; color: white; }
        #updateTime { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Crowd Monitoring Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
            <div id="updateTime">Last updated: Loading...</div>
        </div>
        
        <div id="alerts-container"></div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="count-inside">-</div>
                <div class="stat-label">People Inside</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-entered">-</div>
                <div class="stat-label">Total Entered Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-exited">-</div>
                <div class="stat-label">Total Exited Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="peak-count">-</div>
                <div class="stat-label">Today's Peak Count</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Hourly Distribution Today</h3>
            <canvas id="hourly-chart" width="800" height="400"></canvas>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/admin" class="btn btn-primary">Admin Controls</a>
            <a href="/reports" class="btn btn-primary">View Reports</a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Initialize chart
        const ctx = document.getElementById('hourly-chart').getContext('2d');
        const hourlyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Array.from({length: 24}, (_, i) => i + ':00'),
                datasets: [{
                    label: 'Entries',
                    data: new Array(24).fill(0),
                    backgroundColor: 'rgba(52, 152, 219, 0.6)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        function updateDashboard() {
            // Update counts
            fetch('/api/counts')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('count-inside').textContent = data.data.count_inside;
                        document.getElementById('total-entered').textContent = data.data.total_entered;
                        document.getElementById('total-exited').textContent = data.data.total_exited;
                    }
                })
                .catch(error => console.error('Error fetching counts:', error));
            
            // Update daily stats
            fetch('/api/daily-stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const dailyStats = data.data.daily_stats;
                        const hourlyData = data.data.hourly_breakdown;
                        
                        document.getElementById('peak-count').textContent = dailyStats.peak_count || 0;
                        
                        // Update hourly chart
                        const entries = new Array(24).fill(0);
                        hourlyData.forEach(hour => {
                            entries[hour.hour] = hour.entries || 0;
                        });
                        hourlyChart.data.datasets[0].data = entries;
                        hourlyChart.update();
                    }
                })
                .catch(error => console.error('Error fetching daily stats:', error));
            
            // Update alerts
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const alertsContainer = document.getElementById('alerts-container');
                        alertsContainer.innerHTML = '';
                        
                        data.data.active_alerts.forEach(alert => {
                            const alertDiv = document.createElement('div');
                            alertDiv.className = alert.type === 'crowd_limit' ? 'alert alert-danger' : 'alert alert-warning';
                            alertDiv.innerHTML = `<strong>${alert.type.toUpperCase()}:</strong> ${alert.message}`;
                            alertsContainer.appendChild(alertDiv);
                        });
                    }
                })
                .catch(error => console.error('Error fetching alerts:', error));
            
            // Update timestamp
            document.getElementById('updateTime').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
        
        // Initial load and set interval
        updateDashboard();
        setInterval(updateDashboard, 5000); // Update every 5 seconds
    </script>
</body>
</html>
        '''
        
        # Save dashboard template
        with open(templates_dir / 'dashboard.html', 'w') as f:
            f.write(dashboard_html)
        
        # Create basic admin template
        admin_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crowd Monitor - Admin Panel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #e74c3c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .control-panel { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn-danger { background-color: #e74c3c; color: white; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-success { background-color: #27ae60; color: white; }
        input[type="number"], input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 100px; }
        .result { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Control Panel</h1>
            <p>Administrative functions for the Crowd Monitoring System</p>
        </div>
        
        <div class="control-panel">
            <h3>Count Management</h3>
            <button class="btn btn-danger" onclick="resetCounts()">Reset All Counts</button>
            <div id="reset-result"></div>
        </div>
        
        <div class="control-panel">
            <h3>Crowd Limit Settings</h3>
            <input type="number" id="new-crowd-limit" placeholder="New limit" min="1">
            <button class="btn btn-primary" onclick="updateCrowdLimit()">Update Crowd Limit</button>
            <div id="limit-result"></div>
        </div>
        
        <div class="control-panel">
            <h3>Alert Settings</h3>
            <label><input type="checkbox" id="alerts-enabled"> Enable Alerts</label><br>
            <label><input type="checkbox" id="sound-alerts"> Sound Alerts</label><br>
            <label><input type="checkbox" id="popup-alerts"> Popup Alerts</label><br>
            <input type="number" id="alert-cooldown" placeholder="Cooldown (sec)" min="5">
            <button class="btn btn-primary" onclick="updateAlertSettings()">Update Alert Settings</button>
            <div id="alerts-result"></div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/" class="btn btn-success">Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        function resetCounts() {
            const reason = prompt('Enter reason for reset:') || 'Admin panel reset';
            
            fetch('/api/admin/reset-counts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: reason, admin_user: 'web_admin' })
            })
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById('reset-result');
                result.className = 'result ' + (data.success ? 'success' : 'error');
                result.textContent = data.data ? data.data.message : data.error;
            })
            .catch(error => {
                const result = document.getElementById('reset-result');
                result.className = 'result error';
                result.textContent = 'Error: ' + error.message;
            });
        }
        
        function updateCrowdLimit() {
            const newLimit = parseInt(document.getElementById('new-crowd-limit').value);
            
            if (!newLimit || newLimit <= 0) {
                alert('Please enter a valid crowd limit');
                return;
            }
            
            fetch('/api/admin/update-crowd-limit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_limit: newLimit, admin_user: 'web_admin' })
            })
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById('limit-result');
                result.className = 'result ' + (data.success ? 'success' : 'error');
                result.textContent = data.data ? data.data.message : data.error;
            })
            .catch(error => {
                const result = document.getElementById('limit-result');
                result.className = 'result error';
                result.textContent = 'Error: ' + error.message;
            });
        }
        
        function updateAlertSettings() {
            const settings = {
                alerts_enabled: document.getElementById('alerts-enabled').checked,
                sound_alerts: document.getElementById('sound-alerts').checked,
                popup_alerts: document.getElementById('popup-alerts').checked,
                alert_cooldown: parseInt(document.getElementById('alert-cooldown').value) || null,
                admin_user: 'web_admin'
            };
            
            fetch('/api/admin/update-alert-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById('alerts-result');
                result.className = 'result ' + (data.success ? 'success' : 'error');
                result.textContent = data.data ? data.data.message : data.error;
            })
            .catch(error => {
                const result = document.getElementById('alerts-result');
                result.className = 'result error';
                result.textContent = 'Error: ' + error.message;
            });
        }
    </script>
</body>
</html>
        '''
        
        # Save admin template
        with open(templates_dir / 'admin.html', 'w') as f:
            f.write(admin_html)
        
        # Create reports template
        reports_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crowd Monitor - Reports</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #27ae60; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .report-panel { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn-success { background-color: #27ae60; color: white; }
        .btn-primary { background-color: #3498db; color: white; }
        select, input[type="date"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin: 5px; }
        .result { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reports & Analytics</h1>
            <p>Generate and download crowd reports</p>
        </div>
        
        <div class="report-panel">
            <h3>Generate Report</h3>
            <select id="report-type">
                <option value="daily">Daily Report</option>
                <option value="weekly">Weekly Report</option>
                <option value="monthly">Monthly Report</option>
            </select>
            <input type="date" id="report-date" value="">
            <select id="report-format">
                <option value="csv">CSV Format</option>
                <option value="excel">Excel Format</option>
            </select>
            <button class="btn btn-success" onclick="generateReport()">Generate Report</button>
            <div id="report-result"></div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/" class="btn btn-primary">Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        // Set default date to today
        document.getElementById('report-date').value = new Date().toISOString().split('T')[0];
        
        function generateReport() {
            const reportType = document.getElementById('report-type').value;
            const reportDate = document.getElementById('report-date').value;
            const reportFormat = document.getElementById('report-format').value;
            
            const resultDiv = document.getElementById('report-result');
            resultDiv.innerHTML = 'Generating report...';
            resultDiv.className = 'result';
            
            fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_type: reportType,
                    target_date: reportDate,
                    format: reportFormat,
                    admin_user: 'web_admin'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        Report generated successfully!<br>
                        <a href="${data.data.download_url}" class="btn btn-primary" download>
                            Download ${data.data.filename}
                        </a>
                    `;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.textContent = data.error;
                }
            })
            .catch(error => {
                resultDiv.className = 'result error';
                resultDiv.textContent = 'Error: ' + error.message;
            });
        }
    </script>
</body>
</html>
        '''
        
        # Save reports template
        with open(templates_dir / 'reports.html', 'w') as f:
            f.write(reports_html)
        
        self.logger.info("Dashboard templates created")
    
    def start_server(self, threaded: bool = True):
        """
        Start the Flask server.
        
        Args:
            threaded (bool): Run server in a separate thread
        """
        try:
            # Create templates
            self.create_templates()
            
            # Start data update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_live_data)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            if threaded:
                # Run in separate thread
                server_thread = threading.Thread(
                    target=lambda: self.app.run(
                        host=self.host,
                        port=self.port,
                        debug=False,  # Disable debug in threaded mode
                        use_reloader=False
                    )
                )
                server_thread.daemon = True
                server_thread.start()
                
                self.logger.info(f"Dashboard server started at http://{self.host}:{self.port}")
                return server_thread
            else:
                # Run in main thread
                self.logger.info(f"Starting dashboard server at http://{self.host}:{self.port}")
                self.app.run(host=self.host, port=self.port, debug=self.debug)
        
        except Exception as e:
            self.logger.error(f"Failed to start dashboard server: {e}")
            raise
    
    def stop_server(self):
        """Stop the dashboard server."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
    
    def _update_live_data(self):
        """Background thread to update live data cache."""
        while self.running:
            try:
                # Update counts
                counts = self.db_manager.get_current_count()
                
                # Update alerts
                active_alerts = self.alert_manager.get_active_alerts()
                alerts_data = [
                    {
                        'type': alert.alert_type.value,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat()
                    } for alert in active_alerts
                ]
                
                # Update cache
                self.live_data_cache = {
                    'counts': counts,
                    'alerts': alerts_data,
                    'last_update': datetime.now()
                }
                
            except Exception as e:
                self.logger.error(f"Error updating live data: {e}")
            
            time.sleep(5)  # Update every 5 seconds


def create_dashboard_server(host: str = None, port: int = None) -> DashboardServer:
    """
    Factory function to create a DashboardServer instance.
    
    Args:
        host (str): Host address to bind to
        port (int): Port number to bind to
        
    Returns:
        DashboardServer instance
    """
    return DashboardServer(host=host, port=port)


def main():
    """Run dashboard server as standalone application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crowd Monitor Web Dashboard')
    parser.add_argument('--host', default='localhost', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        dashboard = create_dashboard_server(host=args.host, port=args.port)
        dashboard.debug = args.debug
        dashboard.start_server(threaded=False)
    
    except KeyboardInterrupt:
        print("Dashboard server stopped")
    except Exception as e:
        print(f"Failed to start dashboard: {e}")


if __name__ == "__main__":
    main()