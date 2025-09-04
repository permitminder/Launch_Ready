#!/usr/bin/env python3
"""
GOOD MORNING PERMITMINDER! ☕
Daily environment setup - Python version
Run this every morning: python3 good_morning.py
"""

import os
import sys
import subprocess
import time

def print_header():
    print("\n" + "="*50)
    print("☕ GOOD MORNING PERMITMINDER!")
    print("="*50 + "\n")

def check_and_install_packages():
    """Check and install required packages"""
    print("📦 Checking packages...")
    
    required = ['streamlit', 'pandas', 'openpyxl']
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package} installed")
        except ImportError:
            print(f"  📥 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"  ✅ {package} installed")

def check_files():
    """Check if all required files exist"""
    print("\n📋 Checking files...")
    
    required_files = {
        'pa_exceedances_launch_ready.csv': '❗ DATA FILE',
        'app.py': 'Main app with toggle',
        'search_full.py': 'Premium version',
        'search_free.py': 'Free version',
        'inter_app_enhanced.py': 'Original app'
    }
    
    all_good = True
    for file, description in required_files.items():
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} missing - {description}")
            if file == 'pa_exceedances_launch_ready.csv':
                all_good = False
    
    return all_good

def launch_menu():
    """Show launch options"""
    print("\n" + "="*50)
    print("🚀 READY TO LAUNCH!")
    print("="*50)
    print("\nWhat do you want to run today?")
    print("\n1) app.py (Version toggle)")
    print("2) search_full.py (Premium)")
    print("3) search_free.py (Free)")
    print("4) inter_app_enhanced.py (Original)")
    print("5) Exit (I'll run manually)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    files = {
        '1': 'app.py',
        '2': 'search_full.py',
        '3': 'search_free.py',
        '4': 'inter_app_enhanced.py'
    }
    
    if choice in files:
        file_to_run = files[choice]
        if os.path.exists(file_to_run):
            print(f"\n🚀 Launching {file_to_run}...")
            print("="*50)
            print("Press Ctrl+C to stop the app\n")
            time.sleep(1)
            subprocess.run(["streamlit", "run", file_to_run])
        else:
            print(f"\n❌ {file_to_run} not found!")
            print("Create the file first or choose another option")
    elif choice == '5':
        print("\n✅ Environment ready!")
        print("To run manually, use:")
        print("  streamlit run [filename.py]")
    else:
        print("\n✅ Environment ready! Run manually with:")
        print("  streamlit run app.py")

def main():
    print_header()
    
    # Check Python version
    print(f"🐍 Python version: {sys.version.split()[0]}")
    
    # Check and install packages
    check_and_install_packages()
    
    # Check files
    files_ok = check_files()
    
    if not files_ok:
        print("\n⚠️  Warning: Data file missing!")
        print("Make sure pa_exceedances_launch_ready.csv is in this folder")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Launch menu
    launch_menu()

if __name__ == "__main__":
    main()