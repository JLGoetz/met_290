import time
import os
from dotenv import load_dotenv
from rtde_receive import RTDEReceiveInterface
from rtde_control import RTDEControlInterface
from d_client import DashboardClient

load_dotenv()

def run_service_check(node_id, ip):
    print(f"\n--- STARTING SERVICE CHECK: NODE {node_id} ({ip}) ---")
    
    try:
        # 1. CONNECT TO DASHBOARD (Port 29999)
        print(f"[{node_id}] Connecting to Dashboard Server...")
        db = DashboardClient(ip)
        db.connect()
        
        # Check Status
        status = db.robotmode()
        print(f"[{node_id}] Current Status: {status}")

        if "POWER_OFF" in status:
            cmd = input(f"[{node_id}] Robot is OFF. Power On & Release Brakes? (y/n): ")
            if cmd.lower() == 'y':
                print(f"[{node_id}] Powering on...")
                db.powerOn()
                time.sleep(4)
                print(f"[{node_id}] Releasing Brakes...")
                db.brakeRelease()
                time.sleep(4)
        
        db.disconnect()

        # 2. CONNECT TO RTDE (Port 30004/30013)
        print(f"[{node_id}] Testing RTDE Data Stream...")
        rtde_r = RTDEReceiveInterface(ip)
        pose = rtde_r.getActualTCPPose()
        
        if pose:
            print(f"✅ SUCCESS: Node {node_id} is LIVE.")
            print(f"   Current TCP Pose: {pose}")
        else:
            print(f"⚠️ RTDE Connected, but pose data is empty.")

    except Exception as e:
        print(f"❌ ERROR on Node {node_id}: {e}")

if __name__ == "__main__":
    # Choose which robot to test (1-4)
    target = input("Which Robot Node do you want to test? (1-4): ")
    ip = os.getenv(f'ROBOT_{target}_IP')
    
    if ip:
        run_service_check(target, ip)
    else:
        print("Invalid Node or IP not found in .env")