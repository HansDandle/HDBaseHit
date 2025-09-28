#!/usr/bin/env python3
"""
LineDrive Setup Launcher
Handles dependency checking and launches appropriate setup interface
"""

import sys
import subprocess
import os
from pathlib import Path

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def install_tkinter_instructions():
    """Provide instructions for installing tkinter"""
    system = sys.platform.lower()
    
    print("\n" + "="*60)
    print("TKINTER NOT AVAILABLE")
    print("="*60)
    print("The GUI setup requires tkinter, which is not installed.")
    print("\nInstallation instructions:")
    
    if system.startswith("win"):
        print("• On Windows: Reinstall Python from python.org with 'tcl/tk and IDLE' checked")
        print("• Or install via: pip install tk")
    elif system.startswith("darwin"):  # macOS
        print("• On macOS: brew install python-tk")
        print("• Or: pip install tk")
    elif system.startswith("linux"):
        print("• On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("• On CentOS/RHEL: sudo yum install tkinter")
        print("• Or: pip install tk")
    else:
        print("• Try: pip install tk")
    
    print("\nFalling back to console setup...")
    print("="*60 + "\n")

def main():
    """Main launcher function"""
    print("🚀 LineDrive Setup Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("dvr_web.py").exists():
        print("❌ Error: Please run this from the LineDrive directory")
        print("   (The directory containing dvr_web.py)")
        input("\nPress Enter to exit...")
        return 1
    
    # Try GUI setup first if tkinter is available
    if check_tkinter():
        print("🖥️  Launching GUI setup...")
        try:
            result = subprocess.run([sys.executable, "setup_gui.py"])
            return result.returncode
        except FileNotFoundError:
            print("❌ setup_gui.py not found, falling back to console setup")
        except Exception as e:
            print(f"❌ GUI setup failed: {e}")
            print("   Falling back to console setup...")
    else:
        install_tkinter_instructions()
    
    # Fallback to console setup
    print("📱 Launching console setup...")
    try:
        if Path("setup.py").exists():
            result = subprocess.run([sys.executable, "setup.py"])
            return result.returncode
        else:
            print("❌ No setup scripts found!")
            input("\nPress Enter to exit...")
            return 1
    except Exception as e:
        print(f"❌ Console setup failed: {e}")
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())