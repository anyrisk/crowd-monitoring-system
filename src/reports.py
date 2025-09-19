"""
Reports generation module for the Smart Temple People Counter.
Generates daily/weekly/monthly visitor summaries and exports to CSV/Excel formats.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
import os

from utils.config import get_config
from utils.logger import default_logger
from src.database import get_database_manager


class ReportGenerator:
    """
    Generates various types of reports from the people counter data.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize report generator.
        
        Args:
            logger (logging.Logger): Logger instance
        """
        self.config = get_config()
        self.logger = logger or default_logger
        self.db_manager = get_database_manager()
        
        # Report settings
        self.reports_dir = self.config.REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up matplotlib for report generation
        plt.style.use('default')
        sns.set_palette("husl")
    
    def generate_daily_report(self, target_date: date = None) -> Dict[str, Any]:
        """
        Generate comprehensive daily visitor report.
        
        Args:
            target_date (date): Date to generate report for (default: today)
            
        Returns:
            Dictionary containing report data
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            self.logger.info(f"Generating daily report for {target_date}")
            
            # Get daily statistics
            daily_stats = self.db_manager.get_daily_stats(target_date)
            
            # Get hourly distribution
            hourly_data = self.db_manager.get_hourly_distribution(target_date)
            
            # Get all events for the day
            events_data = self.db_manager.get_events_by_date_range(target_date, target_date)
            
            # Calculate additional metrics
            report_data = {
                'date': target_date,
                'summary': daily_stats,
                'hourly_breakdown': hourly_data,
                'total_events': len(events_data),
                'peak_hour': self._find_peak_hour(hourly_data),
                'busiest_periods': self._find_busy_periods(hourly_data),
                'visit_patterns': self._analyze_visit_patterns(events_data),
                'performance_metrics': self._calculate_performance_metrics(events_data)
            }
            
            return report_data
        
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return {}
    
    def generate_weekly_report(self, start_date: date = None) -> Dict[str, Any]:
        """
        Generate weekly visitor report.
        
        Args:
            start_date (date): Start date of the week (default: this week's Monday)
            
        Returns:
            Dictionary containing weekly report data
        """
        if start_date is None:
            # Get Monday of current week
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        
        end_date = start_date + timedelta(days=6)
        
        try:
            self.logger.info(f"Generating weekly report for {start_date} to {end_date}")
            
            # Collect daily data for the week
            weekly_data = []
            total_visitors = 0
            peak_day = None
            peak_count = 0
            
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                daily_stats = self.db_manager.get_daily_stats(current_date)
                
                day_visitors = daily_stats.get('total_entries', 0)
                total_visitors += day_visitors
                
                if day_visitors > peak_count:
                    peak_count = day_visitors
                    peak_day = current_date
                
                weekly_data.append({
                    'date': current_date,
                    'day_name': current_date.strftime('%A'),
                    'total_entries': day_visitors,
                    'total_exits': daily_stats.get('total_exits', 0),
                    'peak_count': daily_stats.get('peak_count', 0)
                })
            
            # Calculate weekly metrics
            report_data = {
                'week_start': start_date,
                'week_end': end_date,
                'total_visitors': total_visitors,
                'average_daily_visitors': total_visitors / 7,
                'peak_day': peak_day,
                'peak_day_count': peak_count,
                'daily_breakdown': weekly_data,
                'day_of_week_analysis': self._analyze_day_patterns(weekly_data)
            }
            
            return report_data
        
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            return {}
    
    def generate_monthly_report(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        Generate monthly visitor report.
        
        Args:
            year (int): Year for report (default: current year)
            month (int): Month for report (default: current month)
            
        Returns:
            Dictionary containing monthly report data
        """
        if year is None or month is None:
            today = date.today()
            year = year or today.year
            month = month or today.month
        
        # Get first and last day of month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        try:
            self.logger.info(f"Generating monthly report for {start_date} to {end_date}")
            
            # Collect data for the month
            monthly_stats = []
            total_visitors = 0
            peak_day = None
            peak_count = 0
            
            current_date = start_date
            while current_date <= end_date:
                daily_stats = self.db_manager.get_daily_stats(current_date)
                day_visitors = daily_stats.get('total_entries', 0)
                total_visitors += day_visitors
                
                if day_visitors > peak_count:
                    peak_count = day_visitors
                    peak_day = current_date
                
                monthly_stats.append({
                    'date': current_date,
                    'total_entries': day_visitors,
                    'total_exits': daily_stats.get('total_exits', 0),
                    'peak_count': daily_stats.get('peak_count', 0)
                })
                
                current_date += timedelta(days=1)
            
            # Calculate monthly metrics
            days_in_month = (end_date - start_date).days + 1
            
            report_data = {
                'year': year,
                'month': month,
                'month_name': start_date.strftime('%B'),
                'start_date': start_date,
                'end_date': end_date,
                'total_visitors': total_visitors,
                'average_daily_visitors': total_visitors / days_in_month,
                'peak_day': peak_day,
                'peak_day_count': peak_count,
                'days_in_month': days_in_month,
                'daily_breakdown': monthly_stats,
                'weekly_patterns': self._analyze_weekly_patterns(monthly_stats, start_date)
            }
            
            return report_data
        
        except Exception as e:
            self.logger.error(f"Error generating monthly report: {e}")
            return {}
    
    def export_to_csv(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        Export report data to CSV format.
        
        Args:
            report_data: Report data dictionary
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"temple_report_{timestamp}.csv"
            
            filepath = self.reports_dir / filename
            
            # Convert report data to DataFrame
            if 'daily_breakdown' in report_data:
                df = pd.DataFrame(report_data['daily_breakdown'])
            elif 'hourly_breakdown' in report_data:
                df = pd.DataFrame(report_data['hourly_breakdown'])
            else:
                # Create summary DataFrame
                df = pd.DataFrame([report_data])
            
            # Export to CSV
            df.to_csv(filepath, index=False)
            
            self.logger.info(f"Report exported to CSV: {filepath}")
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return ""
    
    def export_to_excel(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """
        Export report data to Excel format with multiple sheets.
        
        Args:
            report_data: Report data dictionary
            filename: Output filename (optional)
            
        Returns:
            Path to exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"temple_report_{timestamp}.xlsx"
            
            filepath = self.reports_dir / filename
            
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                # Summary sheet
                if 'summary' in report_data:
                    summary_df = pd.DataFrame([report_data['summary']])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed breakdown
                if 'daily_breakdown' in report_data:
                    daily_df = pd.DataFrame(report_data['daily_breakdown'])
                    daily_df.to_excel(writer, sheet_name='Daily_Data', index=False)
                
                if 'hourly_breakdown' in report_data:
                    hourly_df = pd.DataFrame(report_data['hourly_breakdown'])
                    hourly_df.to_excel(writer, sheet_name='Hourly_Data', index=False)
            
            self.logger.info(f"Report exported to Excel: {filepath}")
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            return ""
    
    def generate_charts(self, report_data: Dict[str, Any], 
                       chart_types: List[str] = None) -> List[str]:
        """
        Generate visualization charts from report data.
        
        Args:
            report_data: Report data dictionary
            chart_types: List of chart types to generate
            
        Returns:
            List of paths to generated chart files
        """
        if chart_types is None:
            chart_types = ['daily_visitors', 'hourly_distribution', 'weekly_trends']
        
        chart_files = []
        
        try:
            for chart_type in chart_types:
                filepath = self._generate_single_chart(report_data, chart_type)
                if filepath:
                    chart_files.append(filepath)
            
            return chart_files
        
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
            return []
    
    def _generate_single_chart(self, report_data: Dict[str, Any], 
                              chart_type: str) -> Optional[str]:
        """Generate a single chart based on type."""
        try:
            plt.figure(figsize=(12, 8))
            
            if chart_type == 'daily_visitors' and 'daily_breakdown' in report_data:
                # Daily visitors chart
                daily_data = report_data['daily_breakdown']
                df = pd.DataFrame(daily_data)
                
                plt.plot(df['date'], df['total_entries'], marker='o', linewidth=2)
                plt.title('Daily Visitor Count', fontsize=16)
                plt.xlabel('Date')
                plt.ylabel('Number of Visitors')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
            
            elif chart_type == 'hourly_distribution' and 'hourly_breakdown' in report_data:
                # Hourly distribution chart
                hourly_data = report_data['hourly_breakdown']
                df = pd.DataFrame(hourly_data)
                
                plt.bar(df['hour'], df['entries'], alpha=0.7, color='skyblue')
                plt.title('Hourly Visitor Distribution', fontsize=16)
                plt.xlabel('Hour of Day')
                plt.ylabel('Number of Entries')
                plt.grid(True, alpha=0.3)
            
            elif chart_type == 'weekly_trends' and 'daily_breakdown' in report_data:
                # Weekly trends chart
                daily_data = report_data['daily_breakdown']
                df = pd.DataFrame(daily_data)
                
                if 'day_name' in df.columns:
                    plt.bar(df['day_name'], df['total_entries'], alpha=0.7, color='lightgreen')
                    plt.title('Weekly Visitor Trends', fontsize=16)
                    plt.xlabel('Day of Week')
                    plt.ylabel('Number of Visitors')
                    plt.xticks(rotation=45)
                
            else:
                return None
            
            # Save chart
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{chart_type}_{timestamp}.png"
            filepath = self.reports_dir / filename
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
        
        except Exception as e:
            self.logger.error(f"Error generating chart {chart_type}: {e}")
            plt.close()
            return None
    
    def _find_peak_hour(self, hourly_data: List[Dict]) -> Optional[int]:
        """Find the hour with highest visitor count."""
        if not hourly_data:
            return None
        
        max_entries = 0
        peak_hour = None
        
        for hour_data in hourly_data:
            entries = hour_data.get('entries', 0)
            if entries > max_entries:
                max_entries = entries
                peak_hour = hour_data.get('hour')
        
        return peak_hour
    
    def _find_busy_periods(self, hourly_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify busy periods during the day."""
        if not hourly_data:
            return []
        
        # Calculate average entries
        total_entries = sum(hour.get('entries', 0) for hour in hourly_data)
        avg_entries = total_entries / len(hourly_data) if hourly_data else 0
        
        # Find periods above average
        busy_periods = []
        for hour_data in hourly_data:
            entries = hour_data.get('entries', 0)
            if entries > avg_entries * 1.5:  # 50% above average
                busy_periods.append({
                    'hour': hour_data.get('hour'),
                    'entries': entries,
                    'ratio_to_average': entries / avg_entries if avg_entries > 0 else 0
                })
        
        return sorted(busy_periods, key=lambda x: x['entries'], reverse=True)
    
    def _analyze_visit_patterns(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Analyze visit patterns from event data."""
        if not events_data:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(events_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        # Entry/exit patterns
        entries = df[df['event_type'] == 'entry']
        exits = df[df['event_type'] == 'exit']
        
        patterns = {
            'total_entries': len(entries),
            'total_exits': len(exits),
            'peak_entry_hour': entries['hour'].mode().iloc[0] if not entries.empty else None,
            'peak_exit_hour': exits['hour'].mode().iloc[0] if not exits.empty else None,
            'average_stay_indication': len(entries) - len(exits)  # Rough indication
        }
        
        return patterns
    
    def _calculate_performance_metrics(self, events_data: List[Dict]) -> Dict[str, Any]:
        """Calculate system performance metrics."""
        if not events_data:
            return {}
        
        # Time-based analysis
        df = pd.DataFrame(events_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate event frequency
        time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600  # hours
        events_per_hour = len(df) / time_span if time_span > 0 else 0
        
        metrics = {
            'total_events': len(df),
            'events_per_hour': events_per_hour,
            'detection_confidence_avg': df['confidence'].mean() if 'confidence' in df.columns else None,
            'time_span_hours': time_span
        }
        
        return metrics
    
    def _analyze_day_patterns(self, weekly_data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns across days of the week."""
        if not weekly_data:
            return {}
        
        df = pd.DataFrame(weekly_data)
        
        return {
            'busiest_day': df.loc[df['total_entries'].idxmax(), 'day_name'] if not df.empty else None,
            'quietest_day': df.loc[df['total_entries'].idxmin(), 'day_name'] if not df.empty else None,
            'weekend_vs_weekday': self._compare_weekend_weekday(df)
        }
    
    def _analyze_weekly_patterns(self, monthly_stats: List[Dict], start_date: date) -> Dict[str, Any]:
        """Analyze weekly patterns within a month."""
        if not monthly_stats:
            return {}
        
        # Group by weeks
        weeks = {}
        for stat in monthly_stats:
            stat_date = stat['date']
            # Calculate week number
            week_start = stat_date - timedelta(days=stat_date.weekday())
            week_key = week_start.strftime("%Y-W%U")
            
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(stat)
        
        # Calculate weekly totals
        weekly_totals = []
        for week_key, week_data in weeks.items():
            total_visitors = sum(day['total_entries'] for day in week_data)
            weekly_totals.append({
                'week': week_key,
                'total_visitors': total_visitors,
                'days_count': len(week_data)
            })
        
        return {
            'weeks_count': len(weekly_totals),
            'weekly_breakdown': weekly_totals
        }
    
    def _compare_weekend_weekday(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compare weekend vs weekday visitor patterns."""
        weekend_days = ['Saturday', 'Sunday']
        
        weekend_data = df[df['day_name'].isin(weekend_days)]
        weekday_data = df[~df['day_name'].isin(weekend_days)]
        
        return {
            'weekend_avg': weekend_data['total_entries'].mean() if not weekend_data.empty else 0,
            'weekday_avg': weekday_data['total_entries'].mean() if not weekday_data.empty else 0,
            'weekend_total': weekend_data['total_entries'].sum() if not weekend_data.empty else 0,
            'weekday_total': weekday_data['total_entries'].sum() if not weekday_data.empty else 0
        }


def create_report_generator() -> ReportGenerator:
    """
    Factory function to create a ReportGenerator instance.
    
    Returns:
        ReportGenerator instance
    """
    return ReportGenerator()