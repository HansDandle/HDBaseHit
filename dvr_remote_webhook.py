"""
Simple webhook service for triggering DVR restart from phone.
Run this as a separate service on a different port.
"""

from flask import Flask, request, jsonify
import subprocess
import os
import threading

webhook_app = Flask(__name__)

@webhook_app.route('/trigger/dvr-restart', methods=['POST', 'GET'])
def trigger_dvr_restart():
    """Webhook to restart DVR with Prowlarr"""
    try:
        # Security: Check for a simple token
        auth_token = request.args.get('token') or request.json.get('token') if request.json else None
        
        if auth_token != 'your-secret-token-here':
            return jsonify({"error": "Invalid token"}), 401
        
        # Kill existing DVR
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                         capture_output=True, timeout=10)
        except:
            pass
        
        # Start DVR in background
        def start_dvr():
            dvr_dir = os.path.dirname(os.path.abspath(__file__))
            batch_path = os.path.join(dvr_dir, "run_dvr_with_prowlarr.bat")
            subprocess.Popen(['cmd', '/c', batch_path], 
                           cwd=dvr_dir,
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        threading.Thread(target=start_dvr, daemon=True).start()
        
        return jsonify({
            "status": "success",
            "message": "DVR restart initiated",
            "timestamp": "2025-09-25"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_app.route('/status')
def webhook_status():
    """Check if webhook service is alive"""
    return jsonify({"status": "alive", "service": "DVR Remote Control"})

if __name__ == '__main__':
    print("🌐 DVR Remote Control Webhook")
    print("📱 Trigger from phone: http://YOUR_IP:5001/trigger/dvr-restart?token=your-secret-token-here")
    print("🔗 Status check: http://YOUR_IP:5001/status")
    webhook_app.run(host='0.0.0.0', port=5001, debug=False)