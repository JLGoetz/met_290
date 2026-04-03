from django.apps import AppConfig
import os


class RobotControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'robot_control'

    def ready(self):
        """
        This function runs ONCE when Django starts up.
        """
        # The 'RUN_MAIN' check is a Django quirk. 
        # It prevents the PLC thread from starting twice during auto-reload.
        if os.environ.get('RUN_MAIN') == 'true':
            from .engine import framework_engine
            
            print("--- Starting Industrial Framework Engine ---")
            framework_engine.start_all()
