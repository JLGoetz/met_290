from django.shortcuts import render
from .engine import framework_engine  # Import the singleton instance

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
