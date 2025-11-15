# This file allows Railpack to detect and run the FastAPI application
# It imports the app from the backend directory
import sys
import os
import importlib.util

# Get the path to backend/main.py
backend_main_path = os.path.join(os.path.dirname(__file__), 'backend', 'main.py')

# Load the module from backend/main.py
spec = importlib.util.spec_from_file_location("backend_main", backend_main_path)
backend_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main)

# Get the app from the backend module
app = backend_main.app

# This allows Railpack to detect it as a FastAPI app
__all__ = ['app']

