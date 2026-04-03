import threading
import time
import os
from django import db
from dotenv import load_dotenv
from pycomm3 import LogixDriver
from rtde_receive import RTDEReceiveInterface
from rtde_control import RTDEControlInterface
from d_client import DashboardClient

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
        self.pose = {'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}
        self.connected = False
        self.status = "DISCONNECTED"
        # If IP is local, we treat it as a Virtual Robot (No socket attempt)
        # Ensure this line isn't accidentally hardcoded to True
        self.is_virtual = (ip == "127.0.0.1" or ip is None)
        self.mode = "POWER_OFF"

    def action_power_on(self):
        """Remotely triggers Power On and Brake Release."""
        try:
            db = DashboardClient(self.ip)
            db.connect()
            db.powerOn()
            time.sleep(3)
            db.brakeRelease()
            db.disconnect()
            return True
        except Exception as e:
            print(f"Power On Error Node {self.node_id}: {e}")
            return False
        
    def run(self):
        if self.is_virtual:
            print(f"[ROBOT {self.node_id}] Starting VIRTUAL MODE (No Network)")
            self.connected = True # Force connected to True for the HMI
            import random
            while True:
                # Just move the Z-axis slightly so we see life on the HMI
                # Inside the Virtual Mode loop:
                self.pose = {
                    'x': 0.0,
                    'y': 0.0,
                    'z': 0.5 + (random.random() * 0.005),
                    'rx': 0.0,
                    'ry': 0.0,
                    'rz': 0.0
                }
                time.sleep(0.5)
        else:
            # ONLY try to connect if it's a real Lab IP
            print(f"[ROBOT {self.node_id}] Attempting REAL connection to {self.ip}...")
            while True:
                try:
                    from rtde_receive import RTDEReceiveInterface
                    from d_client import DashboardClient
    
                    db = DashboardClient(self.ip)
                    db.connect()
                    rtde_r = RTDEReceiveInterface(self.ip)
                    self.connected = True
                    while True:
                        # Get the actual state from the Dashboard Server
                        # Returns: 'POWER_OFF', 'IDLE' (Ready), 'BOOTING', etc.
                        self.status = db.robotmode() 
                        
                        p = rtde_r.getActualTCPPose()
                        self.pose = {'x': p[0], 'y': p[1], 'z': p[2]}
                        time.sleep(0.1)

                except Exception as e:
                    self.connected = False
                    self.status = "DISCONNECTED"
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

    def send_movement(self, node_id, target_pose):
        """Safety-Interlocked Movement Command."""
        # 1. Check the physical PLC Master Enable (Switch 0)
        if not self.plc.data.get('master_enable', False):
            print("🛑 COMMAND REJECTED: PLC Master Enable is OFF")
            return False

        # 2. Check if this specific node is selected on the PLC (Switches 4-7)
        if self.plc.data.get('active_node') != node_id:
            print(f"⚠️ COMMAND REJECTED: Node {node_id} is not selected on PLC console.")
            return False

        # 3. If safety passes, send the RTDE command
        # (We will build the actual MoveL/MoveJ logic next)
        print(f"🚀 Moving Robot {node_id} to {target_pose}")
        return True

# Global Instance for Django to import
framework_engine = SystemManager()