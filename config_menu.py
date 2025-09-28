"""
Configuration menu system for TV Recorder
Provides user-friendly menus for managing settings
"""

import os
import sys
import json
from pathlib import Path
from config_manager import get_config, reload_config

class ConfigMenu:
    def __init__(self):
        self.config = get_config()
    
    def show_main_menu(self):
        """Show main configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    TV Recorder Configuration Menu")
            print("=" * 50)
            print()
            print("1. HDHomeRun Settings")
            print("2. Directory Settings") 
            print("3. FFmpeg Settings")
            print("4. Prowlarr Integration")
            print("5. Web Interface Settings")
            print("6. View Current Configuration")
            print("7. Save & Exit")
            print("8. Exit Without Saving")
            print()
            
            choice = input("Select option (1-8): ").strip()
            
            if choice == '1':
                self.hdhr_menu()
            elif choice == '2':
                self.directories_menu()
            elif choice == '3':
                self.ffmpeg_menu()
            elif choice == '4':
                self.prowlarr_menu()
            elif choice == '5':
                self.web_interface_menu()
            elif choice == '6':
                self.view_config()
            elif choice == '7':
                self.save_and_exit()
                break
            elif choice == '8':
                print("Exiting without saving...")
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def hdhr_menu(self):
        """HDHomeRun configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    HDHomeRun Settings")
            print("=" * 50)
            print()
            current_ip = self.config.get_hdhr_ip()
            print(f"Current IP Address: {current_ip}")
            print()
            print("1. Change IP Address")
            print("2. Test Connection")
            print("3. Auto-discover HDHomeRun")
            print("4. Back to Main Menu")
            print()
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                new_ip = input(f"Enter new IP address [{current_ip}]: ").strip()
                if new_ip:
                    self.config.set('hdhr', 'ip_address', new_ip)
                    print(f"IP address updated to: {new_ip}")
                    input("Press Enter to continue...")
            elif choice == '2':
                self.test_hdhr_connection()
            elif choice == '3':
                self.discover_hdhr()
            elif choice == '4':
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def directories_menu(self):
        """Directory configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    Directory Settings")
            print("=" * 50)
            print()
            print(f"Recordings: {self.config.get('directories', 'recordings')}")
            print(f"TV Shows:   {self.config.get('directories', 'tv_shows')}")
            print(f"Movies:     {self.config.get('directories', 'movies')}")
            print()
            print("1. Change Recordings Directory")
            print("2. Change TV Shows Directory") 
            print("3. Change Movies Directory")
            print("4. Create Missing Directories")
            print("5. Back to Main Menu")
            print()
            
            choice = input("Select option (1-5): ").strip()
            
            if choice == '1':
                self.change_directory('recordings', 'Recordings')
            elif choice == '2':
                self.change_directory('tv_shows', 'TV Shows')
            elif choice == '3':
                self.change_directory('movies', 'Movies')
            elif choice == '4':
                self.create_directories()
            elif choice == '5':
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def ffmpeg_menu(self):
        """FFmpeg configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    FFmpeg Settings")
            print("=" * 50)
            print()
            current_path = self.config.get_ffmpeg_path()
            print(f"Current FFmpeg Path: {current_path}")
            print()
            print("1. Change FFmpeg Path")
            print("2. Test FFmpeg")
            print("3. Auto-find FFmpeg")
            print("4. Back to Main Menu")
            print()
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                new_path = input(f"Enter FFmpeg path [{current_path}]: ").strip()
                if new_path:
                    self.config.set('ffmpeg', 'path', new_path)
                    print(f"FFmpeg path updated to: {new_path}")
                    input("Press Enter to continue...")
            elif choice == '2':
                self.test_ffmpeg()
            elif choice == '3':
                self.find_ffmpeg()
            elif choice == '4':
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def prowlarr_menu(self):
        """Prowlarr configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    Prowlarr Integration")
            print("=" * 50)
            print()
            enabled = self.config.is_prowlarr_enabled()
            prowlarr_config = self.config.get_prowlarr_config()
            
            print(f"Enabled: {'Yes' if enabled else 'No'}")
            print(f"API URL: {prowlarr_config['api_url']}")
            print(f"API Key: {'*' * len(prowlarr_config['api_key']) if prowlarr_config['api_key'] else 'Not set'}")
            print()
            print("1. Enable/Disable Prowlarr")
            print("2. Change API URL")
            print("3. Change API Key")
            print("4. Test Connection")
            print("5. Back to Main Menu")
            print()
            
            choice = input("Select option (1-5): ").strip()
            
            if choice == '1':
                self.config.set('prowlarr', 'enabled', not enabled)
                status = "enabled" if not enabled else "disabled"
                print(f"Prowlarr {status}")
                input("Press Enter to continue...")
            elif choice == '2':
                new_url = input(f"Enter API URL [{prowlarr_config['api_url']}]: ").strip()
                if new_url:
                    self.config.set('prowlarr', 'api_url', new_url)
                    print(f"API URL updated to: {new_url}")
                    input("Press Enter to continue...")
            elif choice == '3':
                new_key = input("Enter API Key: ").strip()
                if new_key:
                    self.config.set('prowlarr', 'api_key', new_key)
                    print("API key updated")
                    input("Press Enter to continue...")
            elif choice == '4':
                self.test_prowlarr()
            elif choice == '5':
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def web_interface_menu(self):
        """Web interface configuration menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("    Web Interface Settings")
            print("=" * 50)
            print()
            web_config = self.config.get_web_config()
            
            print(f"Host: {web_config['host']}")
            print(f"Port: {web_config['port']}")
            print(f"Debug: {'Yes' if web_config['debug'] else 'No'}")
            print()
            print("1. Change Host")
            print("2. Change Port") 
            print("3. Toggle Debug Mode")
            print("4. Back to Main Menu")
            print()
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == '1':
                new_host = input(f"Enter host [{web_config['host']}]: ").strip()
                if new_host:
                    self.config.set('web_interface', 'host', new_host)
                    print(f"Host updated to: {new_host}")
                    input("Press Enter to continue...")
            elif choice == '2':
                try:
                    new_port = input(f"Enter port [{web_config['port']}]: ").strip()
                    if new_port:
                        port_num = int(new_port)
                        if 1 <= port_num <= 65535:
                            self.config.set('web_interface', 'port', port_num)
                            print(f"Port updated to: {port_num}")
                        else:
                            print("Port must be between 1 and 65535")
                        input("Press Enter to continue...")
                except ValueError:
                    print("Invalid port number")
                    input("Press Enter to continue...")
            elif choice == '3':
                new_debug = not web_config['debug']
                self.config.set('web_interface', 'debug', new_debug)
                print(f"Debug mode {'enabled' if new_debug else 'disabled'}")
                input("Press Enter to continue...")
            elif choice == '4':
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def view_config(self):
        """Display current configuration"""
        self.clear_screen()
        print("=" * 50)
        print("    Current Configuration")
        print("=" * 50)
        print()
        print(json.dumps(self.config.config, indent=2))
        print()
        input("Press Enter to continue...")
    
    def save_and_exit(self):
        """Save configuration and exit"""
        try:
            self.config.save_config()
            print("Configuration saved successfully!")
            print(f"Saved to: {self.config.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
        input("Press Enter to continue...")
    
    # Helper methods
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def change_directory(self, key, label):
        """Change directory setting"""
        current = self.config.get('directories', key)
        new_dir = input(f"Enter {label} directory [{current}]: ").strip()
        if new_dir:
            self.config.set('directories', key, new_dir)
            print(f"{label} directory updated to: {new_dir}")
            
            # Offer to create directory
            create = input("Create directory if it doesn't exist? [y/N]: ").strip().lower()
            if create in ['y', 'yes']:
                try:
                    expanded_path = self.config.expand_path(new_dir)
                    expanded_path.mkdir(parents=True, exist_ok=True)
                    print(f"Directory created: {expanded_path}")
                except Exception as e:
                    print(f"Error creating directory: {e}")
            
            input("Press Enter to continue...")
    
    def create_directories(self):
        """Create all configured directories"""
        dirs = ['recordings', 'tv_shows', 'movies']
        created = []
        errors = []
        
        for dir_key in dirs:
            try:
                dir_path = self.config.get('directories', dir_key)
                expanded_path = self.config.expand_path(dir_path)
                expanded_path.mkdir(parents=True, exist_ok=True)
                created.append(str(expanded_path))
            except Exception as e:
                errors.append(f"{dir_key}: {e}")
        
        if created:
            print("Created directories:")
            for dir_path in created:
                print(f"  {dir_path}")
        
        if errors:
            print("\\nErrors:")
            for error in errors:
                print(f"  {error}")
        
        input("\\nPress Enter to continue...")
    
    def test_hdhr_connection(self):
        """Test HDHomeRun connection"""
        import requests
        
        ip = self.config.get_hdhr_ip()
        print(f"Testing connection to HDHomeRun at {ip}...")
        
        try:
            response = requests.get(f"http://{ip}/lineup.json", timeout=5)
            if response.status_code == 200:
                lineup = response.json()
                print(f"✓ Connected successfully!")
                print(f"Found {len(lineup)} channels")
            else:
                print(f"✗ Connection failed: HTTP {response.status_code}")
        except requests.RequestException as e:
            print(f"✗ Connection failed: {e}")
        
        input("Press Enter to continue...")
    
    def discover_hdhr(self):
        """Auto-discover HDHomeRun devices"""
        print("Scanning network for HDHomeRun devices...")
        # Implementation would go here - similar to setup.py
        print("This feature is not yet implemented.")
        input("Press Enter to continue...")
    
    def test_ffmpeg(self):
        """Test FFmpeg installation"""
        import subprocess
        
        ffmpeg_path = self.config.get_ffmpeg_path()
        print(f"Testing FFmpeg at: {ffmpeg_path}")
        
        try:
            result = subprocess.run([ffmpeg_path, "-version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Extract version info
                version_line = result.stdout.split('\\n')[0]
                print(f"✓ FFmpeg found: {version_line}")
            else:
                print(f"✗ FFmpeg test failed: {result.stderr}")
        except FileNotFoundError:
            print(f"✗ FFmpeg not found at: {ffmpeg_path}")
        except subprocess.TimeoutExpired:
            print(f"✗ FFmpeg test timed out")
        except Exception as e:
            print(f"✗ FFmpeg test error: {e}")
        
        input("Press Enter to continue...")
    
    def find_ffmpeg(self):
        """Auto-find FFmpeg installation"""
        import subprocess
        
        print("Searching for FFmpeg...")
        
        # Common locations to check
        locations = [
            "ffmpeg",
            "C:\\\\ffmpeg\\\\bin\\\\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg"
        ]
        
        found = []
        for location in locations:
            try:
                result = subprocess.run([location, "-version"], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    found.append(location)
            except:
                pass
        
        if found:
            print(f"Found FFmpeg installations:")
            for i, path in enumerate(found, 1):
                print(f"  {i}. {path}")
            
            try:
                choice = int(input(f"Select installation (1-{len(found)}): ")) - 1
                if 0 <= choice < len(found):
                    selected_path = found[choice]
                    self.config.set('ffmpeg', 'path', selected_path)
                    print(f"FFmpeg path updated to: {selected_path}")
            except (ValueError, IndexError):
                print("Invalid choice")
        else:
            print("No FFmpeg installations found")
        
        input("Press Enter to continue...")
    
    def test_prowlarr(self):
        """Test Prowlarr connection"""
        import requests
        
        if not self.config.is_prowlarr_enabled():
            print("Prowlarr is disabled")
            input("Press Enter to continue...")
            return
        
        prowlarr_config = self.config.get_prowlarr_config()
        api_url = prowlarr_config['api_url']
        api_key = prowlarr_config['api_key']
        
        if not api_key:
            print("API key not configured")
            input("Press Enter to continue...")
            return
        
        print(f"Testing Prowlarr connection to {api_url}...")
        
        try:
            headers = {"X-Api-Key": api_key}
            response = requests.get(f"{api_url}/api/v1/indexer", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                indexers = response.json()
                print(f"✓ Connected successfully!")
                print(f"Found {len(indexers)} indexers")
            else:
                print(f"✗ Connection failed: HTTP {response.status_code}")
        except requests.RequestException as e:
            print(f"✗ Connection failed: {e}")
        
        input("Press Enter to continue...")

def main():
    """Run configuration menu"""
    menu = ConfigMenu()
    menu.show_main_menu()

if __name__ == "__main__":
    main()