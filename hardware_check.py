import socket
import os
from dotenv import load_dotenv

load_dotenv()

def check_robot(node_id, ip):
    port = 30003 # UR Real-time port
    try:
        # 2-second timeout so we don't hang forever
        s = socket.create_connection((ip, port), timeout=2)
        print(f"✅ NODE {node_id} ({ip}): ONLINE")
        s.close()
    except Exception:
        print(f"❌ NODE {node_id} ({ip}): OFFLINE / UNREACHABLE")

if __name__ == "__main__":
    nodes = [
        (1, os.getenv('ROBOT_1_IP')),
        (2, os.getenv('ROBOT_2_IP')),
        (3, os.getenv('ROBOT_3_IP')),
        (4, os.getenv('ROBOT_4_IP')),
    ]
    
    print("--- Scanning 4-Node Cluster ---")
    for node_id, ip in nodes:
        check_robot(node_id, ip)