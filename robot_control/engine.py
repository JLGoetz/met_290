import threading
import time
import os
from dotenv import load_dotenv
from pycomm3 import LogixDriver
from rtde_receive import RTDEReceiveInterface
from rtde_control import RTDEControlInterface

# Load the .env file
load_dotenv()

class PLCHandler:
    """Handles the Allen-Bradley L27 Connection and UDT Mapping."""
    def __init__(self, ip):
        self.ip = ip
        self.data = {}
        self.connected = False

    def run(self):
        while True:
            try:
                with LogixDriver(self.ip) as plc:
                    self.connected = True
                    print(f"[PLC] Connected to {self.ip}")
                    while True:
                        # Read the entire UDT structures in one go for efficiency
                        controls = plc.read('Framework_Controls')
                        telemetry = plc.read('AI_Telemetry')
                        
                        if controls and telemetry:
                            self.data = {
                                'controls': controls.value,
                                'telemetry': telemetry.value
                            }
                        time.sleep(0.1) # 10Hz
            except Exception as e:
                self.connected = False
                print(f"[PLC ERROR] {e}. Retrying in 5s...")
                time.sleep(5)

class RobotNode:
    """Handles an individual UR3e via RTDE."""
    def __init__(self, node_id, ip):
        self.node_id = node_id
        self.ip = ip
        self.pose = []
        self.connected = False
        # If IP is local, we treat it as a Virtual Robot (No socket attempt)
        self.is_virtual = (ip == "127.0.0.1")

    def run(self):
        if self.is_virtual:
            print(f"[ROBOT {self.node_id}] Starting VIRTUAL MODE (No Network)")
            self.connected = True # Force connected to True for the HMI
            import random
            while True:
                # Just move the Z-axis slightly so we see life on the HMI
                self.pose[2] = 0.5 + (random.random() * 0.005)
                time.sleep(0.5)
        else:
            # ONLY try to connect if it's a real Lab IP
            print(f"[ROBOT {self.node_id}] Attempting REAL connection to {self.ip}...")
            while True:
                try:
                    from rtde_receive import RTDEReceiveInterface
                    rtde_r = RTDEReceiveInterface(self.ip)
                    self.connected = True
                    while True:
                        self.pose = rtde_r.getActualTCPPose()
                        time.sleep(0.05)
                except Exception as e:
                    self.connected = False
                    print(f"[ROBOT {self.node_id}] Offline. Retrying {self.ip}...")
                    time.sleep(10) # Wait longer between retries to keep terminal clean

class SystemManager:
    """The 'Brain' that coordinates the threads using Environment Variables."""
    def __init__(self):
        # Pull IPs from .env with a fallback default
        self.plc = PLCHandler(os.getenv('PLC_IP', '127.0.0.1'))
        
        self.nodes = {
            1: RobotNode(1, os.getenv('ROBOT_1_IP')),
            2: RobotNode(2, os.getenv('ROBOT_2_IP')),
            3: RobotNode(3, os.getenv('ROBOT_3_IP')),
            4: RobotNode(4, os.getenv('ROBOT_4_IP')),
        }

    def start_all(self):
        # Start PLC Thread
        threading.Thread(target=self.plc.run, daemon=True).start()
        # Start Robot Threads
        for node in self.nodes.values():
            threading.Thread(target=node.run, daemon=True).start()

# Global Instance for Django to import
framework_engine = SystemManager()