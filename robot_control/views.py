from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # <--- THIS IS THE MISSING LINE
from .engine import framework_engine
from dashboard_client import DashboardClient
import time

def dashboard(request):
    """Initial page load (The Shell)."""
    return render(request, 'dashboard.html')

def update_status(request):
    """The HTMX pulse (The Data)."""
    # Grab the current state of the PLC and all 4 Robots
    context = {
        'plc': framework_engine.plc.data.get('controls', {}),
        'plc_connected': framework_engine.plc.connected,
        'nodes': framework_engine.nodes,  # This passes the RobotNode objects
    }
    # Send ONLY the small status_display.html fragment back to the browser
    return render(request, 'partials/status_display.html', context)
# Create your views here.

@csrf_exempt # <--- ADD THIS
def toggle_power(request, node_id):
    node = framework_engine.nodes.get(int(node_id))
    if not node:
        return JsonResponse({"error": "Node not found"}, status=404)
    
    db = DashboardClient(node.ip)
    db.connect()
    current = db.robotmode()
    
    if "POWER_OFF" in current:
        db.powerOn()
    elif "POWER_ON" in current:
        db.brakeRelease()
    elif "RUNNING" in current or "IDLE" in current:
        db.powerOff() # Shutdown for safety
        
    db.disconnect()
    return render(request, 'partials/status_display.html', {'node': node})

@csrf_exempt
def move_home(request, node_id):
    """Triggers the home move if PLC safety allows it."""
    # 1. Get the PLC state from our background engine
    plc_safe = framework_engine.plc.data.get('master_enable', False)
    
    if not plc_safe:
        return JsonResponse({"status": "ERROR", "message": "PLC MASTER ENABLE IS OFF!"}, status=403)

    # 2. Find the robot and trigger the move
    node = framework_engine.nodes.get(int(node_id))
    if node and node.connected:
        success = node.move_to_home() # This calls the method in your engine.py
        return JsonResponse({"status": "SUCCESS" if success else "FAILED"})
    
    return JsonResponse({"status": "ERROR", "message": "Node not found or offline."})
