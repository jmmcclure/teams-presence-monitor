# Install as a Windows Service with NSSM

1. Download NSSM:
   https://nssm.cc/download
2. Open an Administrator Command Prompt
3. Run:
4. Set:
- Application path: `C:\Path\To\python.exe`
- Arguments: `teams_monitor.py`
- Startup directory: Project folder
5. Install and run the service:


Logs will appear in `/logs`, and your service will auto-restart with the watchdog.

