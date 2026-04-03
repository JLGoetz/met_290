from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt  # <--- THIS IS THE MISSING LINE
from dashboard_client import DashboardClient
import time

def hello_world(request):
    return HttpResponse("<h1>Hello World</h1><p>The Django Framework is stable and hardware-free.</p>")
