"""
LineDrive Windows Service Wrapper
Install this to make LineDrive auto-start and always run

DISCLAIMER: LineDrive is not affiliated with Silicondust USA Inc.
HDHomeRun is a registered trademark of Silicondust USA Inc. This is an independent project.
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time

class DVRService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TVRecorderDVR"
    _svc_display_name_ = "LineDrive DVR Service"
    _svc_description_ = "TV Recording service with Prowlarr integration"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        self.main()
        
    def main(self):
        # Change to DVR directory (current working directory)
        dvr_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(dvr_dir)
        
        while self.is_alive:
            try:
                # Start DVR process
                proc = subprocess.Popen([
                    sys.executable, 'dvr_web.py'
                ], cwd=dvr_dir)
                
                # Wait for either service stop or process end
                while self.is_alive and proc.poll() is None:
                    # Check every 5 seconds
                    if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0:
                        proc.terminate()
                        break
                        
                if not self.is_alive:
                    break
                    
                # If we get here, the DVR process ended unexpectedly
                servicemanager.LogErrorMsg(f"DVR process ended unexpectedly, restarting in 30 seconds...")
                time.sleep(30)
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error in DVR service: {e}")
                time.sleep(30)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(DVRService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(DVRService)