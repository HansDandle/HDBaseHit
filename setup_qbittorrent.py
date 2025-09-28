#!/usr/bin/env python3

"""
qBittorrent Web UI Setup Helper
"""

import requests
import webbrowser
import time

def check_qbittorrent_webui():
    """Check if qBittorrent Web UI is accessible"""
    QB_HOST = "http://localhost:8080"
    
    print("🔍 Checking qBittorrent Web UI...")
    
    try:
        # Try to access the web interface
        response = requests.get(f"{QB_HOST}/", timeout=5)
        if response.status_code == 200:
            print("✅ qBittorrent Web UI is accessible!")
            print(f"📍 Web UI URL: {QB_HOST}")
            return True
        else:
            print(f"❌ Web UI responded with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to qBittorrent Web UI")
        print("   Make sure qBittorrent is running and Web UI is enabled")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_login():
    """Test API login functionality"""
    QB_HOST = "http://localhost:8080"
    
    print("\n🔑 Testing API login...")
    
    # Try default credentials
    credentials = [
        {"username": "admin", "password": ""},
        {"username": "admin", "password": "admin"},
        {"username": "", "password": ""},
    ]
    
    for creds in credentials:
        try:
            session = requests.Session()
            response = session.post(f"{QB_HOST}/api/v2/auth/login", data=creds, timeout=5)
            
            if response.status_code == 200 and response.text == "Ok.":
                print(f"✅ Login successful with username: '{creds['username']}', password: '{creds['password']}'")
                
                # Test getting version
                version_response = session.get(f"{QB_HOST}/api/v2/app/version")
                if version_response.status_code == 200:
                    version = version_response.text.strip('"')
                    print(f"📦 qBittorrent version: {version}")
                
                return True
            else:
                print(f"❌ Login failed for username: '{creds['username']}'")
                
        except Exception as e:
            print(f"❌ Error testing login: {e}")
    
    return False

def open_webui():
    """Open qBittorrent Web UI in browser"""
    QB_HOST = "http://localhost:8080"
    print(f"\n🌐 Opening Web UI in browser: {QB_HOST}")
    try:
        webbrowser.open(QB_HOST)
        return True
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        return False

if __name__ == "__main__":
    print("=== qBittorrent Web UI Setup Helper ===\n")
    
    # Check if Web UI is accessible
    if check_qbittorrent_webui():
        # Test API login
        if test_api_login():
            print("\n🎉 qBittorrent Web UI is fully configured!")
            print("\nYou can now use download commands like:")
            print("  'download magnet:?xt=...'")
            print("  'download http://example.com/file.torrent'")
        else:
            print("\n⚠️  Web UI is accessible but login failed")
            print("Please check your username/password settings")
        
        # Offer to open in browser
        response = input("\nOpen Web UI in browser? (y/n): ").lower().strip()
        if response == 'y':
            open_webui()
    else:
        print("\n📋 Setup Instructions:")
        print("1. Make sure qBittorrent is running")
        print("2. Go to Tools → Options → Web UI")
        print("3. Enable 'Web User Interface (Remote control)'")
        print("4. Set IP: * or 127.0.0.1")
        print("5. Set Port: 8080")
        print("6. Set Username: admin")
        print("7. Set Password: (leave blank or set a password)")
        print("8. Click OK and restart qBittorrent if needed")
        print(f"\n9. Then try accessing: http://localhost:8080")