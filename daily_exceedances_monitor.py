# check_new_violations.py - Finds genuinely new violations vs yesterday
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import hashlib

class NewViolationDetector:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def get_today_filename(self):
        """Generate filename for today's violations"""
        return f"{self.data_dir}/violations_{datetime.now().strftime('%Y_%m_%d')}.csv"
    
    def get_yesterday_filename(self):
        """Generate filename for yesterday's violations"""
        yesterday = datetime.now() - timedelta(days=1)
        return f"{self.data_dir}/violations_{yesterday.strftime('%Y_%m_%d')}.csv"
    
    def create_violation_hash(self, violation_row):
        """Create unique hash for violation to detect duplicates"""
        # Use permit + parameter + date + value to create unique ID
        key_parts = [
            str(violation_row.get('PERMIT_NUMBER', '')),
            str(violation_row.get('PARAMETER', '')),
            str(violation_row.get('NON_COMPLIANCE_DATE', '')),
            str(violation_row.get('SAMPLE_VALUE', ''))
        ]
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def load_violations_file(self, filename):
        """Load violations CSV and add hash column"""
        try:
            df = pd.read_csv(filename)
            if df.empty:
                return df
            
            # Add hash column for comparison
            df['violation_hash'] = df.apply(self.create_violation_hash, axis=1)
            return df
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return pd.DataFrame()
    
    def find_new_violations(self, recent_days=30):
        """Find violations that are new compared to yesterday"""
        
        # Load today's and yesterday's data
        today_file = self.get_today_filename()
        yesterday_file = self.get_yesterday_filename()
        
        print(f"Checking for new violations...")
        print(f"Today's file: {today_file}")
        print(f"Yesterday's file: {yesterday_file}")
        
        today_df = self.load_violations_file(today_file)
        yesterday_df = self.load_violations_file(yesterday_file)
        
        if today_df.empty:
            print("No today's violations found")
            return pd.DataFrame()
        
        print(f"Today's violations: {len(today_df)}")
        print(f"Yesterday's violations: {len(yesterday_df)}")
        
        # If no yesterday file, all violations are "new" but filter by date
        if yesterday_df.empty:
            print("No yesterday file - filtering by recent dates only")
            new_violations = self.filter_recent_violations(today_df, recent_days)
        else:
            # Find violations with hashes not in yesterday's data
            yesterday_hashes = set(yesterday_df['violation_hash'])
            new_violations = today_df[~today_df['violation_hash'].isin(yesterday_hashes)]
            
            # Also filter by date to ignore old violations that might appear
            new_violations = self.filter_recent_violations(new_violations, recent_days)
        
        print(f"New violations found: {len(new_violations)}")
        return new_violations
    
    def filter_recent_violations(self, df, recent_days=30):
        """Filter to violations from recent days only"""
        if df.empty:
            return df
        
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        
        # Convert date column to datetime
        df['date_check'] = pd.to_datetime(df['NON_COMPLIANCE_DATE'], errors='coerce')
        
        # Filter to recent violations
        recent_df = df[df['date_check'] >= cutoff_date].copy()
        
        print(f"Filtered to {len(recent_df)} recent violations (last {recent_days} days)")
        return recent_df
    
    def save_new_violations(self, new_violations_df):
        """Save new violations for alert processing"""
        if new_violations_df.empty:
            return None
        
        filename = f"{self.data_dir}/new_violations_{datetime.now().strftime('%Y_%m_%d')}.csv"
        new_violations_df.to_csv(filename, index=False)
        print(f"Saved {len(new_violations_df)} new violations to {filename}")
        return filename
    
    def run_daily_check(self):
        """Main function to run daily new violation detection"""
        print(f"\n=== Daily Violation Check - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
        
        # Find new violations
        new_violations = self.find_new_violations()
        
        if new_violations.empty:
            print("No new violations detected today")
            return None
        
        # Save new violations file
        new_violations_file = self.save_new_violations(new_violations)
        
        # Log summary
        print(f"\n=== Summary ===")
        print(f"New violations: {len(new_violations)}")
        
        # Show breakdown by severity
        if 'Severity' in new_violations.columns:
            severity_counts = new_violations['Severity'].value_counts()
            for severity, count in severity_counts.items():
                print(f"  {severity}: {count}")
        
        return new_violations_file

# daily_scraper.py - Runs your existing scraper and saves with date
import subprocess
import sys
from datetime import datetime
import shutil

class DailyScraper:
    def __init__(self):
        self.today_str = datetime.now().strftime('%Y_%m_%d')
        
    def run_scraper(self):
        """Run your existing PA eDMR scraper"""
        print(f"Running PA eDMR scraper for {self.today_str}...")
        
        try:
            # Run your existing scraper script
            # Replace 'your_scraper.py' with your actual scraper filename
            result = subprocess.run([
                sys.executable, 'process_violations.py'
            ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                print("Scraper completed successfully")
                
                # Move the output file to dated version
                source_file = 'pa_violations_launch_ready.csv'
                dest_file = f'data/violations_{self.today_str}.csv'
                
                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                    print(f"Saved daily data to {dest_file}")
                    return dest_file
                else:
                    print(f"Warning: Expected output file {source_file} not found")
                    return None
            else:
                print(f"Scraper failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Scraper timed out after 30 minutes")
            return None
        except Exception as e:
            print(f"Error running scraper: {e}")
            return None

# daily_alerts.py - Send alerts for new violations only
import csv

class DailyAlertSystem:
    def __init__(self, gmail_email=None, gmail_password=None):
        self.gmail_email = gmail_email
        self.gmail_password = gmail_password
        
    def load_subscriptions(self):
        """Load email subscriptions from Streamlit app"""
        subscriptions = {}
        
        try:
            with open('alert_subscriptions.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row['email']
                    permits = row['permits'].split(',')
                    
                    if email not in subscriptions:
                        subscriptions[email] = {
                            'permits': [],
                            'frequency': row.get('frequency', 'daily')
                        }
                    
                    subscriptions[email]['permits'].extend(permits)
            
            print(f"Loaded {len(subscriptions)} email subscriptions")
            return subscriptions
            
        except FileNotFoundError:
            print("No subscriptions file found")
            return {}
    
    def filter_violations_for_subscriber(self, violations_df, subscriber_permits):
        """Filter violations to only those for subscribed permits"""
        if violations_df.empty:
            return violations_df
        
        return violations_df[violations_df['PERMIT_NUMBER'].isin(subscriber_permits)]
    
    def send_daily_alerts(self, new_violations_file):
        """Send alerts for today's new violations"""
        if not new_violations_file or not os.path.exists(new_violations_file):
            print("No new violations file to process")
            return
        
        # Load new violations
        new_violations = pd.read_csv(new_violations_file)
        if new_violations.empty:
            print("No new violations to alert on")
            return
        
        # Load subscriptions
        subscriptions = self.load_subscriptions()
        if not subscriptions:
            print("No subscriptions - no alerts to send")
            return
        
        print(f"Processing alerts for {len(new_violations)} new violations")
        
        # Send alerts to each subscriber
        alerts_sent = 0
        for email, settings in subscriptions.items():
            
            # Filter violations for this subscriber's permits
            subscriber_violations = self.filter_violations_for_subscriber(
                new_violations, settings['permits']
            )
            
            if not subscriber_violations.empty:
                success = self.send_violation_alert(email, subscriber_violations)
                if success:
                    alerts_sent += 1
                    
        print(f"Sent {alerts_sent} alert emails")
    
    def send_violation_alert(self, email, violations_df):
        """Send individual violation alert email"""
        # Import your existing alert system
        from violation_alerts import ViolationAlertSystem
        
        alert_system = ViolationAlertSystem(self.gmail_email, self.gmail_password)
        
        # Convert DataFrame to violation format
        violations_list = []
        for _, row in violations_df.iterrows():
            violations_list.append({
                'permit': row['PERMIT_NUMBER'],
                'facility': row['PF_NAME'],
                'county': row['COUNTY_NAME'],
                'date': row['NON_COMPLIANCE_DATE'],
                'parameter': row['PARAMETER'],
                'exceedance_percent': row.get('Percent_Over_Limit', 'N/A'),
                'severity': row.get('Severity', 'Unknown'),
                'sample_value': row.get('SAMPLE_VALUE', 'N/A'),
                'permit_value': row.get('PERMIT_VALUE', 'N/A'),
                'unit': row.get('UNIT_OF_MEASURE', 'N/A')
            })
        
        # Format and send email
        subject, body = alert_system.format_alert_email(violations_list, email)
        if subject and body:
            return alert_system.send_email(email, subject, body)
        
        return False

# main.py - Orchestrates the daily monitoring process
def main():
    """Main daily monitoring process"""
    print(f"\n{'='*60}")
    print(f"PERMITMINDER DAILY MONITORING")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Step 1: Run scraper to get today's data
    scraper = DailyScraper()
    scraper_result = scraper.run_scraper()
    
    if not scraper_result:
        print("❌ Scraper failed - aborting daily check")
        return False
    
    # Step 2: Detect new violations vs yesterday
    detector = NewViolationDetector()
    new_violations_file = detector.run_daily_check()
    
    # Step 3: Send alerts for new violations
    if new_violations_file:
        # Get email credentials from environment variables
        gmail_email = os.environ.get('GMAIL_EMAIL')
        gmail_password = os.environ.get('GMAIL_PASSWORD')
        
        alert_system = DailyAlertSystem(gmail_email, gmail_password)
        alert_system.send_daily_alerts(new_violations_file)
    
    print(f"\n✅ Daily monitoring completed at {datetime.now().strftime('%H:%M:%S')}")
    return True

if __name__ == "__main__":
    main()
