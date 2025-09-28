#!/usr/bin/env python3
"""
Interactive setup script for TV Recorder
Helps users configure the application on first run
"""

import json
import os
import sys
import subprocess
from pathlib import Path
import requests
import socket

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("    TV Recorder for HDHomeRun - Interactive Setup")
    print("=" * 60)
    print()

def test_ffmpeg(ffmpeg_path):
    """Test if ffmpeg is available"""
    try:
        result = subprocess.run([ffmpeg_path, "-version"], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def find_hdhr_devices():
    """Try to discover HDHomeRun devices on the network"""
    print("Scanning for HDHomeRun devices on your network...")
    devices = []
    
    # Common IP ranges to scan
    import ipaddress
    import threading
    import queue
    
    def check_ip(ip, result_queue):
        try:
            response = requests.get(f"http://{ip}/discover.json", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if "DeviceID" in data:
                    result_queue.put(ip)
        except:
            pass
    
    # Get local network range
    try:
        # Get default gateway to determine network range
        import subprocess
        if os.name == 'nt':  # Windows
            result = subprocess.run(['route', 'print', '0.0.0.0'], capture_output=True, text=True)
            # Parse to find gateway (simplified)
            gateway_ip = "192.168.1.1"  # Default fallback
        else:  # Unix-like
            result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
            gateway_ip = "192.168.1.1"  # Default fallback
        
        # Scan common ranges
        network_bases = ["192.168.1", "192.168.0", "10.0.0", "10.0.1"]
        
    except:
        network_bases = ["192.168.1", "192.168.0"]
    
    result_queue = queue.Queue()
    threads = []
    
    for base in network_bases:
        for i in range(1, 255):
            ip = f"{base}.{i}"
            thread = threading.Thread(target=check_ip, args=(ip, result_queue))
            threads.append(thread)
            thread.start()
    
    # Wait for threads (with timeout)
    for thread in threads:
        thread.join(timeout=0.1)
    
    # Collect results
    while not result_queue.empty():
        devices.append(result_queue.get())
    
    return devices

def get_user_input(prompt, default=None, validator=None):
    """Get user input with validation"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if validator:
            valid, message = validator(user_input)
            if not valid:
                print(f"Error: {message}")
                continue
        
        return user_input

def validate_ip(ip):
    """Validate IP address"""
    try:
        socket.inet_aton(ip)
        return True, ""
    except socket.error:
        return False, "Invalid IP address format"

def validate_directory(path):
    """Validate directory path"""
    try:
        expanded_path = Path(path).expanduser()
        return True, ""
    except Exception as e:
        return False, str(e)

def validate_port(port_str):
    """Validate port number"""
    try:
        port = int(port_str)
        if 1 <= port <= 65535:
            return True, ""
        else:
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Port must be a number"

def setup_hdhr():
    """Setup HDHomeRun configuration"""
    print("\n--- HDHomeRun Configuration ---")
    print("Looking for HDHomeRun devices...")
    
    devices = find_hdhr_devices()
    
    if devices:
        print(f"Found {len(devices)} potential HDHomeRun device(s):")
        for i, device in enumerate(devices, 1):
            print(f"  {i}. {device}")
        
        if len(devices) == 1:
            return devices[0]
        else:
            while True:
                try:
                    choice = input(f"Select device (1-{len(devices)}) or enter custom IP: ")
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(devices):
                            return devices[idx]
                    else:
                        valid, message = validate_ip(choice)
                        if valid:
                            return choice
                        print(f"Error: {message}")
                except ValueError:
                    print("Please enter a number or valid IP address")
    else:
        print("No HDHomeRun devices found automatically.")
        print("Please enter the IP address of your HDHomeRun device.")
        return get_user_input("HDHomeRun IP address", "192.168.1.100", validate_ip)

def setup_directories():
    """Setup directory configuration"""
    print("\n--- Directory Configuration ---")
    print("Configure where recordings and media will be stored.")
    
    recordings_dir = get_user_input(
        "Recordings directory", 
        str(Path.home() / "TV_Recordings"),
        validate_directory
    )
    
    tv_shows_dir = get_user_input(
        "TV Shows directory", 
        str(Path.home() / "TV Shows"),
        validate_directory
    )
    
    movies_dir = get_user_input(
        "Movies directory", 
        str(Path.home() / "Movies"),
        validate_directory
    )
    
    return {
        "recordings": recordings_dir,
        "tv_shows": tv_shows_dir,
        "movies": movies_dir
    }

def setup_ffmpeg():
    """Setup FFmpeg configuration"""
    print("\n--- FFmpeg Configuration ---")
    print("FFmpeg is required for recording TV streams.")
    
    # Try common locations
    common_paths = [
        "ffmpeg",  # In PATH
        "C:\\ffmpeg\\bin\\ffmpeg.exe",  # Common Windows location
        "/usr/bin/ffmpeg",  # Common Linux location
        "/usr/local/bin/ffmpeg",  # Homebrew on macOS
    ]
    
    working_path = None
    for path in common_paths:
        if test_ffmpeg(path):
            working_path = path
            break
    
    if working_path:
        print(f"Found FFmpeg at: {working_path}")
        use_found = input("Use this FFmpeg? [Y/n]: ").strip().lower()
        if use_found in ['', 'y', 'yes']:
            return working_path
    
    print("FFmpeg not found automatically.")
    print("Please download FFmpeg from https://ffmpeg.org/download.html")
    
    while True:
        ffmpeg_path = input("Enter path to ffmpeg executable [ffmpeg]: ").strip()
        if not ffmpeg_path:
            ffmpeg_path = "ffmpeg"
        
        if test_ffmpeg(ffmpeg_path):
            return ffmpeg_path
        else:
            print("FFmpeg not found at that location. Please check the path.")

def setup_prowlarr():
    """Setup Prowlarr configuration"""
    print("\n--- Prowlarr Configuration (Optional) ---")
    print("Prowlarr integration allows searching for TV shows via torrents.")
    
    enable = input("Enable Prowlarr integration? [y/N]: ").strip().lower()
    if enable not in ['y', 'yes']:
        return {"enabled": False}
    
    api_url = get_user_input("Prowlarr API URL", "http://127.0.0.1:9696")
    
    print("\nTo get your Prowlarr API key:")
    print("1. Open Prowlarr web interface")
    print("2. Go to Settings > General")
    print("3. Copy the API Key")
    
    api_key = input("Prowlarr API Key: ").strip()
    
    return {
        "enabled": True,
        "api_url": api_url,
        "api_key": api_key,
        "timeout": 15
    }

def setup_epg():
    """Setup Electronic Program Guide configuration"""
    print("\n--- Electronic Program Guide (EPG) Configuration ---")
    print("EPG provides TV show listings and scheduling information.")
    print("Your zip code determines which TV stations and schedules are available.")
    
    zip_code = input("Enter your zip code [78748]: ").strip()
    if not zip_code:
        zip_code = "78748"
    
    # Test zip code detection
    print(f"\nTesting EPG service for zip code {zip_code}...")
    try:
        from epg_zap2it import detect_headend_id
        headend_id = detect_headend_id(zip_code)
        if headend_id:
            print(f"✓ Successfully detected your TV market!")
            save_headend = input("Save this configuration? [Y/n]: ").strip().lower()
            if save_headend in ['', 'y', 'yes']:
                headend_id_final = headend_id
            else:
                headend_id_final = ""
        else:
            print("⚠ Could not auto-detect your TV market.")
            headend_id_final = input("Enter headend ID manually (or leave empty): ").strip()
    except Exception as e:
        print(f"⚠ EPG test failed: {e}")
        headend_id_final = ""
    
    auto_refresh = input("Enable automatic EPG refresh? [y/N]: ").strip().lower()
    
    return {
        "zip_code": zip_code,
        "headend_id": headend_id_final,
        "timezone": "America/Chicago",  # Could be auto-detected later
        "auto_refresh": auto_refresh in ['y', 'yes'],
        "refresh_hours": [6, 14, 22]
    }

def setup_web_interface():
    """Setup web interface configuration"""
    print("\n--- Web Interface Configuration ---")
    
    host = get_user_input("Host (0.0.0.0 for all interfaces)", "0.0.0.0")
    port = get_user_input("Port", "5000", validate_port)
    
    return {
        "host": host,
        "port": int(port),
        "debug": False
    }

def create_config():
    """Create configuration file"""
    print_banner()
    
    print("This setup wizard will help you configure TV Recorder.")
    print("You can change these settings later by editing config.json")
    print()
    
    # Gather configuration
    hdhr_ip = setup_hdhr()
    directories = setup_directories()
    ffmpeg_path = setup_ffmpeg()
    epg_config = setup_epg()
    prowlarr_config = setup_prowlarr()
    web_config = setup_web_interface()
    
    # Create config structure
    config = {
        "hdhr": {
            "ip_address": hdhr_ip,
            "comment": "IP address of your HDHomeRun tuner device"
        },
        "directories": {
            **directories,
            "comment": "Directory paths for storing recordings and media"
        },
        "ffmpeg": {
            "path": ffmpeg_path,
            "comment": "Path to ffmpeg executable"
        },
        "epg": {
            **epg_config,
            "comment": "Electronic Program Guide settings for TV listings"
        },
        "prowlarr": {
            **prowlarr_config,
            "comment": "Prowlarr integration settings for torrent searching"
        },
        "biratepay": {
            "enabled": False,
            "port": 5055,
            "comment": "BiratePayment integration for premium content access"
        },
        "web_interface": {
            **web_config,
            "comment": "Web interface settings"
        }
    }
    
    # Save configuration
    config_path = Path.cwd() / "config.json"
    
    print(f"\n--- Configuration Summary ---")
    print(f"HDHomeRun IP: {hdhr_ip}")
    print(f"Recordings directory: {directories['recordings']}")
    print(f"FFmpeg path: {ffmpeg_path}")
    print(f"EPG zip code: {epg_config['zip_code']}")
    print(f"EPG auto-refresh: {epg_config['auto_refresh']}")
    print(f"Prowlarr enabled: {prowlarr_config['enabled']}")
    print(f"Web interface: {web_config['host']}:{web_config['port']}")
    print()
    
    save_config = input(f"Save configuration to {config_path}? [Y/n]: ").strip().lower()
    if save_config in ['', 'y', 'yes']:
        # Create directories
        for dir_path in [directories['recordings'], directories['tv_shows'], directories['movies']]:
            try:
                Path(dir_path).expanduser().mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                print(f"Warning: Could not create directory {dir_path}: {e}")
        
        # Save config file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\nConfiguration saved to {config_path}")
        print("\nSetup complete! You can now run the TV Recorder:")
        print("  python dvr_web.py")
        print("\nOr for the GUI version:")
        print("  python Recordtv.py")
    else:
        print("Configuration not saved.")
    
    return config

if __name__ == "__main__":
    try:
        create_config()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)