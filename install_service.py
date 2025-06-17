import win32serviceutil
import win32service
import win32event
import servicemanager
import os
import sys

class TeamsService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TeamsPresenceMonitor"
    _svc_display_name_ = "Teams Presence Monitor"
    _svc_description_ = "Monitors mic/camera usage and reports to MQTT and Home Assistant"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("TeamsPresenceMonitor service started.")
        os.chdir(os.path.dirname(__file__))
        os.system(f'"{sys.executable}" tray_launcher.py')

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(TeamsService)
