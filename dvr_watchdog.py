"""
Lightweight watchdog service for DVR control
Runs a tiny web server that can start/stop the main DVR app
"""

from flask import Flask, jsonify, request
import subprocess
import psutil
import os
import threading
import time

watchdog = Flask(__name__)

# Use current directory for DVR files
DVR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dvr_web.py")
DVR_BATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_dvr_with_prowlarr.bat")

def find_dvr_process():
    """Find running DVR process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'dvr_web.py' in cmdline:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

@watchdog.route('/')
def status():
    """Show simple status page"""
    dvr_proc = find_dvr_process()
    return f'''
    <html><body style="font-family:Arial;background:#181818;color:#f5f5f5;padding:20px;">
    <h1>📺 DVR Watchdog</h1>
    <p><strong>DVR Status:</strong> {'🟢 Running' if dvr_proc else '🔴 Stopped'}</p>
    {f'<p><strong>PID:</strong> {dvr_proc.pid}</p>' if dvr_proc else ''}
    
    <div style="margin:20px 0;">
    <button onclick="fetch('/start',{{method:'POST'}}).then(()=>location.reload())" 
            style="padding:10px 20px;margin:5px;background:#4CAF50;color:white;border:none;border-radius:5px;">
            ▶️ Start DVR
    </button>
    <button onclick="fetch('/stop',{{method:'POST'}}).then(()=>location.reload())" 
            style="padding:10px 20px;margin:5px;background:#f44336;color:white;border:none;border-radius:5px;">
            ⏹️ Stop DVR  
    </button>
    <button onclick="fetch('/restart',{{method:'POST'}}).then(()=>location.reload())" 
            style="padding:10px 20px;margin:5px;background:#FF9800;color:white;border:none;border-radius:5px;">
            🔄 Restart DVR
    </button>
    </div>
    
    <p><small>Access from phone: <a href="http://192.168.1.214:5002">http://192.168.1.214:5002</a></small></p>
    </body></html>
    '''

@watchdog.route('/start', methods=['POST'])
def start_dvr():
    """Start DVR process"""
    if find_dvr_process():
        return jsonify({"status": "already_running"})
    
    try:
        # Start DVR with environment variables
        env = os.environ.copy()
        env.update({
            'PROWLARR_API_KEY': '73acf5d451594332bc2d50bcee137ddf',
            'PROWLARR_API_URL': 'http://127.0.0.1:9696',
            'BIRATEPAY_ENABLED': '1'
        })
        
        subprocess.Popen([
            'python', DVR_SCRIPT
        ], cwd=os.path.dirname(DVR_SCRIPT), env=env)
        
        return jsonify({"status": "started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@watchdog.route('/stop', methods=['POST'])
def stop_dvr():
    """Stop DVR process"""
    dvr_proc = find_dvr_process()
    if not dvr_proc:
        return jsonify({"status": "not_running"})
    
    try:
        dvr_proc.terminate()
        dvr_proc.wait(timeout=10)
        return jsonify({"status": "stopped"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@watchdog.route('/restart', methods=['POST'])
def restart_dvr():
    """Restart DVR process"""
    # Stop first
    dvr_proc = find_dvr_process()
    if dvr_proc:
        try:
            dvr_proc.terminate()
            dvr_proc.wait(timeout=10)
        except:
            pass
    
    # Wait a bit
    time.sleep(2)
    
    # Start again
    return start_dvr()

if __name__ == '__main__':
    print("🐕 DVR Watchdog starting...")
    print("📱 Control from phone: http://192.168.1.214:5002")
    print("🔧 Use this to start/stop DVR when it's not running")
    
    watchdog.run(host='0.0.0.0', port=5002, debug=False)