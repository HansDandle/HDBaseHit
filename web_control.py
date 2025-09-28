"""
Simple web control panel for remote management.
Add this to your DVR web interface for phone control.
"""

# Add this to your dvr_web.py Flask routes

@app.route('/control')
def control_panel():
    """Simple control panel for remote management"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DVR Control Panel</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #181818; color: #f5f5f5; }
            .btn { 
                display: block; 
                width: 100%; 
                padding: 15px; 
                margin: 10px 0; 
                font-size: 18px; 
                background: #0078d4; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer;
            }
            .btn:hover { background: #106ebe; }
            .status { padding: 10px; background: #333; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>📺 DVR Control Panel</h1>
        
        <div class="status">
            <h3>Service Status</h3>
            <p>DVR Web: <span style="color: #4CAF50;">● Running</span></p>
            <p>Prowlarr: <span id="prowlarr-status">Checking...</span></p>
            <p>BiratePay: <span id="biratepay-status">Checking...</span></p>
        </div>
        
        <button class="btn" onclick="restartService()">🔄 Restart DVR Service</button>
        <button class="btn" onclick="restartProwlarr()">📡 Restart with Prowlarr</button>
        <button class="btn" onclick="checkStatus()">📊 Check All Status</button>
        <button class="btn" onclick="viewLogs()">📋 View Recent Logs</button>
        
        <div id="output" style="margin-top: 20px; padding: 10px; background: #222; border-radius: 5px; font-family: monospace; font-size: 12px;"></div>
        
        <script>
            function restartService() {
                fetch('/control/restart', {method: 'POST'})
                    .then(r => r.json())
                    .then(d => document.getElementById('output').innerHTML = JSON.stringify(d, null, 2));
            }
            
            function restartProwlarr() {
                fetch('/control/restart-prowlarr', {method: 'POST'})
                    .then(r => r.json())
                    .then(d => document.getElementById('output').innerHTML = JSON.stringify(d, null, 2));
            }
            
            function checkStatus() {
                fetch('/control/status')
                    .then(r => r.json())
                    .then(d => {
                        document.getElementById('output').innerHTML = JSON.stringify(d, null, 2);
                        document.getElementById('prowlarr-status').innerHTML = d.prowlarr ? '● Connected' : '● Disconnected';
                        document.getElementById('biratepay-status').innerHTML = d.biratepay ? '● Running' : '● Stopped';
                    });
            }
            
            function viewLogs() {
                fetch('/control/logs')
                    .then(r => r.json())
                    .then(d => document.getElementById('output').innerHTML = d.logs);
            }
            
            // Auto-check status on load
            checkStatus();
        </script>
    </body>
    </html>
    '''

@app.route('/control/restart', methods=['POST'])
def restart_service():
    """Restart the DVR service"""
    try:
        import subprocess
        import os
        
        # Kill any existing DVR processes (careful!)
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
        
        # Start the batch file
        batch_path = os.path.join(os.path.dirname(__file__), 'run_dvr_with_prowlarr.bat')
        subprocess.Popen(['cmd', '/c', batch_path], 
                        cwd=os.path.dirname(__file__),
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        return {"status": "success", "message": "DVR service restarted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/control/restart-prowlarr', methods=['POST'])
def restart_with_prowlarr():
    """Restart with Prowlarr environment"""
    try:
        import subprocess
        import os
        
        # Set environment variables
        os.environ['PROWLARR_API_KEY'] = 'your_prowlarr_api_key_here'
        os.environ['PROWLARR_API_URL'] = 'http://127.0.0.1:9696'
        
        # Test Prowlarr connection
        from prowlarr_client import test_connection
        prowlarr_ok = test_connection()
        
        return {
            "status": "success", 
            "prowlarr_connected": prowlarr_ok,
            "message": f"Environment updated. Prowlarr: {'✅ Connected' if prowlarr_ok else '❌ Failed'}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/control/status')
def service_status():
    """Check status of all services"""
    status = {
        "dvr": True,  # If this responds, DVR is running
        "prowlarr": False,
        "biratepay": False,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        from prowlarr_client import test_connection
        status["prowlarr"] = test_connection()
    except:
        pass
    
    try:
        import requests
        resp = requests.get("http://127.0.0.1:5055/", timeout=2)
        status["biratepay"] = resp.status_code < 500
    except:
        pass
    
    return status

@app.route('/control/logs')
def get_logs():
    """Get recent log entries"""
    try:
        # You could read from log files here
        return {"logs": "Log viewing not implemented yet"}
    except Exception as e:
        return {"logs": f"Error reading logs: {e}"}