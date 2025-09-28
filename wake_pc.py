"""
Enhanced Wake-on-LAN utility with status checking and auto-retry
"""

import socket
import struct
import time
import subprocess
import sys

def get_pc_mac():
    """Auto-detect this PC's MAC address"""
    try:
        result = subprocess.run(['getmac', '/format:value'], 
                              capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith('PhysicalAddress='):
                mac = line.split('=')[1].strip()
                if mac and mac != 'N/A':
                    return mac.replace('-', ':')
    except:
        pass
    return None

def wake_on_lan(mac_address, broadcast_ip='192.168.1.255', port=9):
    """Send WOL magic packet to wake up a computer"""
    try:
        # Clean MAC address
        clean_mac = mac_address.replace(':', '').replace('-', '').replace(' ', '')
        if len(clean_mac) != 12:
            raise ValueError(f"Invalid MAC address: {mac_address}")
            
        mac_bytes = bytes.fromhex(clean_mac)
        
        # Create magic packet: 6 bytes of 0xFF followed by 16 repetitions of MAC
        magic_packet = b'\xFF' * 6 + mac_bytes * 16
        
        # Send via UDP broadcast  
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast_ip, port))
        
        # Also try direct IP if we can determine it
        try:
            # Try to send to specific IP too (some networks need this)
            pc_ip = "YOUR_PC_IP_HERE"  # Replace with your PC's IP
            sock.sendto(magic_packet, (pc_ip, port))
        except:
            pass
            
        sock.close()
        
        print(f"✅ WOL magic packet sent to {mac_address}")
        print(f"📡 Broadcast: {broadcast_ip}:{port}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send WOL packet: {e}")
        return False

def ping_host(host, timeout=1):
    """Check if host is responding to ping"""
    try:
        # Windows ping command
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), host],
            capture_output=True, text=True, timeout=timeout + 2
        )
        return result.returncode == 0
    except:
        return False

def check_dvr_running(host="YOUR_PC_IP_HERE", port=5000, timeout=2):
    """Check if DVR web service is responding"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def wake_and_wait(mac_address, max_wait=120):
    """Wake PC and wait for it to fully boot with DVR running"""
    
    pc_ip = "YOUR_PC_IP_HERE"  # Replace with your PC's actual IP
    
    print(f"🌅 Waking PC with MAC: {mac_address}")
    
    # Check if already awake
    if ping_host(pc_ip):
        print("✅ PC is already awake!")
        if check_dvr_running():
            print("✅ DVR is already running!")
            print(f"🌐 Access at: http://{pc_ip}:5000")
            return True
        else:
            print("⏳ PC awake but DVR not ready yet...")
    else:
        print("😴 PC appears to be sleeping/off")
        
        # Send WOL packet
        if not wake_on_lan(mac_address):
            return False
        
        print("⏳ Waiting for PC to wake up...")
    
    # Wait for PC to respond to ping
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if ping_host(pc_ip, timeout=3):
            print("✅ PC is responding to ping!")
            break
        print(".", end="", flush=True)
        time.sleep(5)
    else:
        print(f"\n❌ PC didn't respond within {max_wait} seconds")
        return False
    
    # Wait for DVR service to start
    print("⏳ Waiting for DVR service to start...")
    while time.time() - start_time < max_wait:
        if check_dvr_running():
            elapsed = int(time.time() - start_time)
            print(f"\n🎉 DVR is ready! (took {elapsed} seconds)")
            print(f"🌐 Access at: http://{pc_ip}:5000")
            return True
        print(".", end="", flush=True)
        time.sleep(3)
    
    print(f"\n⚠️ PC woke up but DVR didn't start within {max_wait} seconds")
    print("Check if Task Scheduler auto-start is configured")
    return False

if __name__ == '__main__':
    # Auto-detect MAC or use hardcoded
    PC_MAC = get_pc_mac() or "A8-6D-AA-35-81-94"  # Your PC's actual MAC address
    
    if len(sys.argv) > 1:
        PC_MAC = sys.argv[1]
    
    print("🖥️  Enhanced Wake-on-LAN for DVR")
    print("=" * 40)
    
    success = wake_and_wait(PC_MAC)
    
    if success:
        print("\n🚀 Ready to use DVR!")
    else:
        print("\n🔧 Troubleshooting tips:")
        print("- Check PC Wake-on-LAN is enabled in BIOS")
        print("- Verify network adapter WOL settings")
        print("- Ensure Task Scheduler auto-start is configured")
        print("- PC should be connected via Ethernet (not WiFi)")
        
    input("\nPress Enter to exit...")