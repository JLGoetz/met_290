import time
# The library name is 'ur_rtde', the module is 'dashboard_client'
from ur_rtde.dashboard_client import DashboardClient 

try:
    db = DashboardClient("192.168.1.10") # Your Node 1 IP
    db.connect()
    print(f"CONNECTED! Robot Mode: {db.robotmode()}")
    db.disconnect()
except Exception as e:
    print(f"ERROR: {e}")