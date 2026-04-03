from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('update-status/', views.update_status, name='update_status'),
    # --- CHECK THIS LINE ---
    path('toggle-power/<int:node_id>/', views.toggle_power, name='toggle_power'),
    
    # Also ensure move-home is ready
    path('move-home/<int:node_id>/', views.move_home, name='move_home'),

]